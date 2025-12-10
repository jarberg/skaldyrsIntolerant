import os
from dataclasses import asdict

import requests

from RESTclients.dataModels import CustomerInvoice
from reconcilliation.utils import recon_data


class UnicontaClient:

    customerDataBase: list

    def __init__(self) -> None:

        self.base_url = os.getenv("ERP_BASE_URL", "https://api.uniconta.com/")
        self.api_key = os.getenv("ERP_API_TOKEN")
        self._username = os.getenv("ERP_USERNAME")
        self._userpass = os.getenv("ERP_PASSWORD")

        self.session = requests.Session()
        self.token = None

        self._debtors_loaded = False
        self._debtors_rows = []
        self._debtors_by_vat = {}

        self.login()

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
            return

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

    def _load_debtors_cache(self):
        """
        Load all debtors from Uniconta once and build an index of ID-like values:
        any field whose key contains 'vat', 'cvr', 'regno' OR is exactly 'Account'
        is treated as an ID / VAT container.
        """
        if self._debtors_loaded:
            return

        #print("[DEBUG] _load_debtors_cache: loading all DebtorClient rows from Uniconta...")

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

        #print(
        #    f"[DEBUG] _load_debtors_cache: loaded {len(self._debtors_rows)} debtors, "
         #   f"{len(self._debtors_by_vat)} distinct ID/VAT keys (VatNumber/CompanyRegNo/Account)."
        #)

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

    def find_deptor_from_invoice(self, invoice):
        if not invoice.customer or invoice.customer.vatID is None:
            return None

        self._load_debtors_cache()

        candidates = self._candidate_vat_values(invoice.customer)
        if not candidates:
            return None

        norm_candidates = [self._normalize_vat(c) for c in candidates if c]
        matchesFound = []

        for nc in norm_candidates:
            if not nc:
                continue
            matches = self._debtors_by_vat.get(nc)
            if matches:
                matchesFound = matches
                break

        if matchesFound is None or len(matchesFound) < 1:
            recon_data.failedList.append(invoice)
            return None

        deptor = matchesFound[0]
        return deptor

    def find_orderNumber(self, debtor, invoice):
        OrderNumber = None

        accountname = debtor.get("Account", "None")
        payload = [
            {
                "PropertyName": "Account",
                "FilterValue": accountname,
                "Skip": 0,
                "Take": 0,
                "OrderBy": "true",
                "OrderByDescending": "false",
            }
        ]

        url = f"{self.base_url}/Query/Get/DebtorOrderClient"
        resp = self.session.post(url, json=payload)
        if not resp.ok:
            raise RuntimeError(f"ERP create_invoice failed: {resp.status_code} {resp.text}")
        data = resp.json()
        if len(data) == 0:
            url = f"{self.base_url}/Crud/Insert/DebtorOrderClient"
            payload = {
                "Account": debtor.get("Account"),
                "Account Name": debtor.get("Account Name"),
                "YourRef": "API-ORDER-001",
                "invoice_date": invoice.period_end,
                "Simulate": "true"
            }
            resp = self.session.post(url, json=payload)
            if not resp.ok:
                raise RuntimeError(f"ERP create_invoice failed: {resp.status_code} {resp.text}")
            data = resp.json()
            OrderNumber = str(data.get("OrderNumber") or data.get("invoiceNumber"))
        else:
            OrderNumber = str(next(iter(data)).get("OrderNumber") or next(iter(data)).get("invoiceNumber"))
        if OrderNumber == "Invalid" or OrderNumber == None:
            pass
            #print("order number not found")
        return OrderNumber

    def create_invoice(self, invoice: CustomerInvoice) -> str:

        deptor = self.find_deptor_from_invoice(invoice)
        if deptor is None:
            return None

        OrderNumber = self.find_orderNumber(deptor, invoice)

        #print(f"Created ERP invoice {OrderNumber} for customer {invoice.customer.name}")

        line_url = f"{self.base_url}/Crud/InsertList/DebtorOrderLineClient"

        all_lines = []
        for category in invoice.categories.values():
            for catline in category.lines:
                all_lines.append({
                    "OrderNumber": OrderNumber,
                    "Item": "CFTEST",
                    "Text": str(catline.ItemName),
                    "Qty": float(catline.Quantity or 0),
                    "Total" : float(catline.Amount or 0),
                    #"Price": float(catline.UnitPrice or 0),
                })

        #print("Sending lines to Uniconta:", all_lines[:3], "...")

        resp = self.session.post(line_url, json=all_lines)
        if not resp.ok:
            raise RuntimeError(
                f"ERP create_invoice failed (lines): {resp.status_code} {resp.text}"
            )

        return OrderNumber


def createUnicontaOrdersWithLines(uniconta_client):
    # Actually create invoices in Uniconta
    for customerInvoice in recon_data.invoiceCustomerdict.values():
        before = len(recon_data.failedList)
        uniconta_client.create_invoice(customerInvoice,)
        after = len(recon_data.failedList)

        # Sum invoice amount: ren Amount (CloudFactory-beløb)
        inv_amount = 0.0
        for category in customerInvoice.categories.values():
            for line in category.lines:
                try:
                    inv_amount += float(line.Amount or 0)
                except (TypeError, ValueError):
                    pass

        if after == before:
            # No new failure added => this invoice was successfully posted
            recon_data.total_amount_success += inv_amount

            cust = customerInvoice.customer
            recon_data.success_rows.append(
                {
                    "Customer ID": cust.id,
                    "Customer Name": cust.name,
                    "VAT": cust.vatID,
                    "Country": cust.countryCode,
                    "Total Amount (DKK)": inv_amount,
                }
            )
        else:
            # This invoice ended up in failedList
            recon_data.total_amount_failed += inv_amount
