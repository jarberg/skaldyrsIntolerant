import os
from dataclasses import asdict

import requests

from RESTclients.dataModels import CustomerInvoice


class UnicontaAdapter:

    customerDataBase: list

    def __init__(self) -> None:

        self.base_url = os.getenv("ERP_BASE_URL", "https://api.uniconta.com/")
        self.api_key = os.getenv("ERP_API_TOKEN") or "5a7ae53b-08cd-4ff0-aa56-60f8ecb8f37c"
        self._username = os.getenv("ERP_USERNAME")
        self._userpass = os.getenv("ERP_PASSWORD")

        self.session = requests.Session()
        self.token = None

        # Local debtor cache
        self._debtors_loaded = False
        self._debtors_rows = []
        # normalized_vat -> list[debtor_row]
        self._debtors_by_vat = {}

        self.login()

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def login(self):
        payload = {
            "Username": self._username,
            "Password": self._userpass,
            "apiKey": self.api_key
        }

        url = f"{self.base_url}/Login"
        r = requests.post(url, json=payload)

        if not r.ok:
            raise RuntimeError(f"Login failed: {r.status_code} {r.text}")

        data = r.json()
        self.token = data.get("token")

        if not self.token:
            raise RuntimeError(f"Login succeeded but no token returned: {data}")

        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

        print("Logged in to Uniconta ✔")

    def ensure_login(self):
        if not self.token:
            self.login()

    # ------------------------------------------------------------------
    # Debug helpers (optional)
    # ------------------------------------------------------------------

    def debug_dump_debtors_sample(self, max_rows: int = 20):
        """
        Fetch a sample of debtors and print keys and VAT-like fields.
        Useful to inspect what Uniconta actually returns.
        """
        url = f"{self.base_url}/Query/Get/DebtorClient"

        payload = [
            {
                "PropertyName": "Account",
                "FilterValue": "",
                "Skip": 0,
                "Take": max_rows,
                "OrderBy": "true",
                "OrderByDescending": "false",
            }
        ]

        resp = self.session.post(url, json=payload)
        if not resp.ok:
            raise RuntimeError(f"debug_dump_debtors_sample failed: {resp.status_code} {resp.text}")

        data = resp.json() or []
        if not data:
            print("[DEBUG] No debtors returned from DebtorClient.")
            return

        print(f"[DEBUG] Got {len(data)} debtor rows. Keys on first row:")
        print(sorted(list(data[0].keys())))

        print("\n[DEBUG] Sample of VAT-like fields (including Account):")
        for row in data:
            name = row.get("Name")
            vat_candidates = {
                k: v
                for k, v in row.items()
                if (
                    any(t in k.lower() for t in ["vat", "cvr", "regno"])
                    or k.lower() == "account"
                )
            }
            print(f"Name={name} → {vat_candidates}")

    # ------------------------------------------------------------------
    # Normalization helper
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_vat(value: str | None) -> str:
        """
        Normalize VAT/ID for matching: remove spaces, dots, dashes, uppercase.
        This is used for:
          - VatNumber
          - CompanyRegNo / CVR
          - Account (when it holds CVR-like values)
        """
        if value is None:
            return ""

        s = str(value).strip()
        s = s.replace(" ", "").replace(".", "").replace("-", "")
        return s.upper()

    # ------------------------------------------------------------------
    # Debtor cache (all ID-like numbers → VAT index)
    # ------------------------------------------------------------------

    def _load_debtors_cache(self):
        """
        Load all debtors from Uniconta once and build an index of ID-like values:
        any field whose key contains 'vat', 'cvr', 'regno' OR is exactly 'Account'
        is treated as an ID / VAT container.
        """
        if self._debtors_loaded:
            return

        print("[DEBUG] _load_debtors_cache: loading all DebtorClient rows from Uniconta...")

        url = f"{self.base_url}/Query/Get/DebtorClient"

        payload = [
            {
                "PropertyName": "Account",
                "FilterValue": "",
                "Skip": 0,
                "Take": 0,
                "OrderBy": "true",
                "OrderByDescending": "false",
            }
        ]

        resp = self.session.post(url, json=payload)
        if not resp.ok:
            raise RuntimeError(f"_load_debtors_cache failed: {resp.status_code} {resp.text}")

        data = resp.json() or []
        self._debtors_rows = data

        by_vat = {}

        for row in data:
            vat_values = set()
            for key, val in row.items():
                if val is None:
                    continue
                key_l = key.lower()
                if (
                    any(t in key_l for t in ["vat", "cvr", "regno"])
                    or key_l == "account"
                ):
                    vat_values.add(str(val))

            for raw_vat in vat_values:
                norm_vat = self._normalize_vat(raw_vat)
                if norm_vat:
                    by_vat.setdefault(norm_vat, []).append(row)

        self._debtors_by_vat = by_vat
        self._debtors_loaded = True

        print(
            f"[DEBUG] _load_debtors_cache: loaded {len(self._debtors_rows)} debtors, "
            f"{len(self._debtors_by_vat)} distinct ID/VAT keys (VatNumber/CompanyRegNo/Account)."
        )

    # ------------------------------------------------------------------
    # VAT candidate builder (from invoice.customer)
    # ------------------------------------------------------------------

    @staticmethod
    def _candidate_vat_values(customer) -> list[str]:
        """
        Build a list of possible VAT/ID formats from CloudFactory VAT
        to try against the unified index (VatNumber, CompanyRegNo, Account).
        We do NOT use Name for matching.
        """
        candidates = set()

        raw = str(customer.vatID or "").strip()
        if not raw:
            return []

        # Raw
        candidates.add(raw)

        # Cleaned
        cleaned = raw.replace(" ", "").replace(".", "").replace("-", "")
        candidates.add(cleaned)

        # Prefix with country code if available
        cc = (customer.countryCode or "").strip()
        if cc:
            candidates.add(cc + cleaned)
            candidates.add(cc.upper() + cleaned)

        # If looks numeric, consider zero-padded (e.g. Danish CVR 8 digits)
        if cleaned.isdigit() and len(cleaned) < 10:
            padded = cleaned.zfill(8)
            candidates.add(padded)
            if cc:
                candidates.add(cc + padded)
                candidates.add(cc.upper() + padded)

        return list(candidates)

    # ------------------------------------------------------------------
    # Debtor lookup (ID/VAT-only matching)
    # ------------------------------------------------------------------

    def find_deptor(self, invoice):

        if not invoice.customer or invoice.customer.vatID is None:
            print("[DEBUG] find_deptor: missing customer or VAT, skipping.")
            return None

        # Make sure cache is available
        self._load_debtors_cache()

        candidates = self._candidate_vat_values(invoice.customer)
        if not candidates:
            print(f"[DEBUG] find_deptor: no VAT candidates for customer {invoice.customer.name}")
            return None

        norm_candidates = [self._normalize_vat(c) for c in candidates if c]

        for nc in norm_candidates:
            if not nc:
                continue
            matches = self._debtors_by_vat.get(nc)
            if matches:
                first = matches[0]
                print(
                    f"[DEBUG] find_deptor: CACHE MATCH by ID/VAT for customer '{invoice.customer.name}' "
                    f"normID='{nc}' → Account={first.get('Account')} Name={first.get('Name')}"
                )
                return matches

        # Nothing found → fail
        print(
            f"[DEBUG] find_deptor: NO ID/VAT MATCH in cache for customer '{invoice.customer.name}' "
            f"VAT candidates={candidates}"
        )
        return []

    # ------------------------------------------------------------------
    # Invoice creation
    # ------------------------------------------------------------------

    def create_invoice(self, invoice: CustomerInvoice, failedlist) -> str:
        """
        Create an invoice in your ERP system.
        Returns the ERP invoice ID/number.
        """
        deptor = self.find_deptor(invoice)

        if deptor is None or len(deptor) < 1:
            print(
                f"[DEBUG] create_invoice: no debtor found for "
                f"{invoice.customer.name} (VAT={invoice.customer.vatID}, "
                f"Country={invoice.customer.countryCode})"
            )
            failedlist.append(invoice)
            return

        deptor = deptor[0]

        payload = {
            "Account": deptor.get("Account"),
            "Account Name": deptor.get("Account Name"),
            "YourRef": "API-ORDER-001",
            "invoice_date": invoice.period_end,
            "Simulate": "true"
        }

        url = f"{self.base_url}/Crud/Insert/DebtorOrderClient"
        resp = self.session.post(url, json=payload)
        if not resp.ok:
            raise RuntimeError(f"ERP create_invoice failed: {resp.status_code} {resp.text}")
        data = resp.json()
        OrderNumber = str(data.get("OrderNumber") or data.get("invoiceNumber"))
        print(f"Created ERP invoice {OrderNumber} for customer {invoice.customer.name}")

        # --- Create order lines ---
        line_url = f"{self.base_url}/Crud/InsertList/DebtorOrderLineClient"

        all_lines = []
        for category in invoice.categories.values():
            for catline in category.lines:
                all_lines.append({
                    "OrderNumber": OrderNumber,
                    "Item": "CFTEST",  # <-- MUST exist in Uniconta inventory
                    "Text": str(catline.ItemName),
                    "Qty": float(catline.Quantity or 0),
                    "Price": float(catline.UnitPrice or 0),
                })

        print("Sending lines to Uniconta:", all_lines[:3], "...")

        resp = self.session.post(line_url, json=all_lines)
        if not resp.ok:
            raise RuntimeError(
                f"ERP create_invoice failed (lines): {resp.status_code} {resp.text}"
            )

        return OrderNumber
