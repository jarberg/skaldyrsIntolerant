import os
from dataclasses import dataclass
from turtledemo.chaos import line
from typing import Optional, Dict, Any, List

import requests

from RESTclients.dataModels import CustomerInvoice
from reconcilliation.utils import report_success_or_failure

class UnicontaClient:

    customerDataBase: list

    def __init__(self) -> None:

        self.company_id = None
        self.base_url = os.getenv("ERP_BASE_URL", "https://api.uniconta.com/")
        self.api_key = os.getenv("ERP_API_TOKEN")
        self._username = os.getenv("ERP_USERNAME")
        self._userpass = os.getenv("ERP_PASSWORD")

        self.session = requests.Session()
        self.token = None

        self._debtors_loaded = False
        self._debtors_rows = []
        self._debtors_by_vat = {}

        self._login()

    def _login(self):
        payload = {
            "Username": self._username,
            "Password": self._userpass,
            "apiKey": self.api_key
        }

        url = f"{self.base_url}Login"
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

        print("Logged in to Uniconta")

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}{path}"
        resp = self.session.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, json: Any, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}{path}"
        resp = self.session.post(url, json=json, params=params)
        resp.raise_for_status()
        return resp

    def get_order_lines_by_order_number(self, order_number: str,) -> List[Dict[str, Any]]:
        return
        payload = [
            {
                "PropertyName": "OrderNumber","FilterValue": order_number,
                "Skip": 0,"Take": 0,
                "OrderBy": "true","OrderByDescending": "false",
            }
        ]

        response = self._post("Query/Get/DebtorOrderLineClient", json=payload)
        if response.ok:
            dictlist =response.json()


    def _ensure_login(self):
        if not self.token:
            self._login()

    def _load_debtors_cache(self):
        """
        Load all debtors from Uniconta once and build an index of ID-like values:
        any field whose key contains 'vat', 'cvr', 'regno' OR is exactly 'Account'
        is treated as an ID / VAT container.
        """
        if self._debtors_loaded:
            return

        #print("[DEBUG] _load_debtors_cache: loading all DebtorClient rows from Uniconta...")

        url = f"{self.base_url}Query/Get/DebtorClient"

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
            report_success_or_failure(invoice, False)
            return None

        self._load_debtors_cache()

        candidates = self._candidate_vat_values(invoice.customer)
        if not candidates:
            report_success_or_failure(invoice, False)
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
            report_success_or_failure(invoice, False)
            return None

        deptor = matchesFound[0]
        return deptor

    def find_orderNumber(self, debtor, invoice):
        OrderNumber = None

        accountname = debtor.get("Account", "None")
        payload = [
            {
                "PropertyName": "Account","FilterValue": accountname,
                "Skip": 0,"Take": 0,
                "OrderBy": "true","OrderByDescending": "false",
            }
        ]

        resp = self._post("Query/Get/DebtorOrderClient", json=payload)
        data = resp.json()

        if len(data) == 0:
            payload = {
                "Account": debtor.get("Account"),
                "Account Name": debtor.get("Account Name"),
                "YourRef": "API-ORDER-001",
                "invoice_date": invoice.period_end,
                "Simulate": "true"
            }
            resp =  self._post("Crud/Insert/DebtorOrderClient", json=payload)

            if not resp.ok:
                raise RuntimeError(f"ERP create_invoice failed: {resp.status_code} {resp.text}")

            data = resp.json()
            OrderNumber = str(data.get("OrderNumber") or data.get("invoiceNumber"))
        else:
            OrderNumber = str(next(iter(data)).get("OrderNumber") or next(iter(data)).get("invoiceNumber"))
        if OrderNumber == "Invalid" or OrderNumber == None:
            pass
            #print("order number not found")
        else:
            self.get_order_lines_by_order_number(OrderNumber)

        return OrderNumber

    def create_uniconta_order_with_lines(self, invoice: CustomerInvoice) -> str:
        error = ""
        deptor = self.find_deptor_from_invoice(invoice)
        if deptor is None:
            return "Could not find deptor for invoice"

        OrderNumber = self.find_orderNumber(deptor, invoice)
        all_lines = []

        for key, category in invoice.categories.items():
            names = lookupDict.get(key)

            for catline in category.lines:
                if catline.Amount != 0.0:
                    price = round(round(catline.UnitPrice, 5) or calculate_price(catline), 6)
                    amount = round(catline.Amount, 2)
                    quantity = catline.Quantity
                    all_lines.append({
                        "OrderNumber": OrderNumber,
                        "mlbEksterntVaregrupp": names.mlbEksterntVaregrupp,
                        "Dimension1": names.Dimension1,
                        "Dimension2": names.Dimension2,
                        "Dimension3": names.Dimension3,
                        "ReferenceNumber": "API_TEST",
                        "Price": price,
                        "Item": names.Item,
                        "Text": str(catline.ItemName),
                        "Currency": catline.Currency,
                        "Qty": quantity,
                        "Total": amount
                    })
        response = self._post("Crud/InsertList/DebtorOrderLineClientUser", json=all_lines)
        report_success_or_failure(invoice, response.ok)

@dataclass
class CategoryNames:
    Item: str
    Dimension1: str
    Dimension2: str
    Dimension3: str
    mlbEksterntVaregrupp: str

lookupDict = {
    "SPLA": CategoryNames("Infrastructure", "InfraS", "Lokal ser", "Backupli2", "Infrastructure"),
    "Microsoft NCE (Azure)": CategoryNames("Labor", "Software", "Azure", "Azure", "Azure"),
    "Microsoft CSP (NCE)": CategoryNames("M365Licenses", "Micr365", "Mic365Lic", "Mic365Lic2", "M365 Licenses"),
    "Dropbox": CategoryNames("Labor", "Software", "Software", "Software", "Software"),
    "Acronis": CategoryNames("Infrastructure", "Software", "Mic36Back", "Mic36Back2", "Infrastructure"),
    "Exclaimer": CategoryNames("Labor", "Software", "Signatur", "Signatur2", "Software"),
    "Keepit": CategoryNames("Infrastructure", "InfraS", "Mic36Back", "Mic36Back2", "Infrastructure"),
    "Impossible cloud": CategoryNames("Infrastructure", "InfraS", "Backup da", "Backupda2", "Infrastructure"),
}


def calculate_price(line):
    if abs(line.Quantity) < 1e-12:
        return 0.0
    return round(float(line.Amount) / float(line.Quantity), 5)
