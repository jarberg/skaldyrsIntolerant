import requests
import os

from datetime import date, datetime
from typing import Dict, Any, List

from RESTclients.dataModels import Customer, CloudFactoryInvoiceCategory, CloudFactoryInvoice

CLOUDFACTORY_EXCHANGE = os.getenv("CLOUDFACTORY_EXCHANGE")
CLOUDFACTORY_PARTNER_ID = os.getenv("CLOUDFACTORY_PARTNER_ID")
CLOUDFACTORY_API_TOKEN = ""
CLOUDFACTORY_BASE_URL = "https://portal.api.cloudfactory.dk/"

if not CLOUDFACTORY_EXCHANGE or not CLOUDFACTORY_PARTNER_ID:
    raise RuntimeError("Missing exchange API credentials. Set CLOUDFATORY_EXCHANGE and CLOUDFATORY_PARTNER_ID.")

class CloudFactoryClient:

    def __init__(self, base_url: str = "", partner_id: str = "") -> None:
        self.base_url = base_url.rstrip("/") or CLOUDFACTORY_BASE_URL.rstrip("/")
        self.partner_id = partner_id or CLOUDFACTORY_PARTNER_ID
        self.session = requests.Session()
        self.accessToken = ""
        self._exchange_token_for_api_token(CLOUDFACTORY_EXCHANGE)
        self.session.headers.update({
            "Authorization": f"Bearer {self.accessToken}",
            "Accept": "application/json",
        })

    def _get(self, path: str, params: Dict[str, Any] = None, type = "json") -> Any:
        if path.startswith("https"):
            url = path
        else:
            url = f"{self.base_url}{path}"
        resp = self.session.get(url, params=params or {})
        if not resp.ok:
            raise RuntimeError(f"CloudFactory GET {url} failed: {resp.status_code} {resp.text}")

        if type == "json":
            return resp.json()
        else:
            return resp.content

    def _exchange_token_for_api_token(self, exchange_token: str) -> str:
        url = self.base_url+"/v1/users/Authentication/exchangeToken?refreshToken="+exchange_token
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "refreshToken": exchange_token,
            "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "client_id": "cloudfactory.partner.portal",  # Example — adjust for your app
            "scope": "api.read api.write offline_access"
        }

        resp = requests.post(url, headers=headers, data=data)
        if not resp.ok:
            raise Exception(f"Token exchange failed: {resp.status_code} {resp.text}")

        token_json = resp.json()
        access_token = token_json.get("accessToken")

        if not access_token:
            raise Exception(f"No access_token returned! Response: {token_json}")
        self.accessToken = access_token
        return access_token

    def list_invoices(self) -> list[CloudFactoryInvoice]:
        """
        Returns all invoices available via CloudFactory Billing API.
        Filters all invoices that reference customers with invalid vat ids
        Pagination supported.
        """
        invoice_list = []

        data = self._get(
            f"/billing/accounts/{self.partner_id}/invoices",
        )
        invoices = data.get("invoices")
        for invoice in invoices:
            periodEndDate = invoice.get("periodEndDate")
            if not periodEndDate:
                continue

            cloudInvoice = CloudFactoryInvoice(self._parse_date(periodEndDate))

            cloudInvoice.extras = dict((x for x in invoice.items()))

            for line in invoice.get("lines"):
                cloudInvoice.categories[line.get("billingTypeDescription")] = CloudFactoryInvoiceCategory(line.get("billingTypeDescription"), line.get("billingDataExcel"))

            invoice_list.append(cloudInvoice)

        return invoice_list

    def fetch_latest_invoices(self) -> (list[CloudFactoryInvoice], bool):
        """
        Returns only the invoices with the latest invoice_date.
        Example:
          invoices = [Sep, Oct, Nov] → returns all Nov invoices only
        """
        invoices = self.list_invoices()
        if not invoices:
            return [], False

        # Determine the latest invoice date
        latest_date = max(inv.endDate for inv in invoices)
        ret_list = [
            inv for inv in invoices
            if inv.endDate == latest_date
        ]
        if not ret_list:
            return [], False

        return ret_list, True

    def list_customers(self) -> List[Customer]:
        """
        Fetch all customers under this partner.
        Adjust endpoint and response fields according to actual API.
        """
        customers: List[Customer] = []
        page = 0
        pageSize = 250
        totalPages = 1

        while page <= totalPages:
            page += 1
            if page > totalPages:
                break

            data = self._get(
                "/v2/customers/Customers",
                params={"PageIndex": page, "PageSize": pageSize}
            )
            totalPages = data.get("metadata").get("totalPages")
            pageSize = data.get("metadata").get("pageSize")
            items = data.get("results") or data  # depends on API style
            if not items:
                break

            for raw in items:
                customer= Customer(
                    id=str(raw["id"]),
                    name=raw.get("name", "Unknown"),
                    vatID=raw.get("vatId", None),
                    countryCode=raw.get("countryCode", None),
                    external_id=raw.get("externalCustomerId", None)  # adjust field name
                )

                customers.append(
                    customer
                )

        return customers

    def fetch_billing_excel(self, excel_url, timeout=60):
        """Download one billingDataExcel file and return it as a DataFrame."""
        if not excel_url:
            raise Exception("excel URL is missing")
        try:
            data = self._get(excel_url, type="excel")
            return data
        except Exception as e:
            short = excel_url[:120] + "..." if len(excel_url) > 120 else excel_url
            print(f"Failed to fetch billingDataExcel {short}: {e}")
            return None

    def fetch_partner_invoices_overview(self,partner_guid):
        url = f"/billing/accounts/{partner_guid}/invoices"
        data =  self._get(url)
        if not data:
            print("⚠ No billing data returned for partner invoices.")
            return None
        return data

    def fetch_invoice_detail(self, invoice_no):
        url = f"billing/accounts/{CLOUDFACTORY_PARTNER_ID}/invoices/{invoice_no}"

        data = self._get(url)
        if not data:
            print(f"⚠ No detail returned for invoice {invoice_no}")
            return None
        return data

    @staticmethod
    def _parse_date(value: str) -> date:
        """
        Parse a date string into a date object.
        Adjust the format to match CloudFactory's response (e.g. "2025-11-01T00:00:00Z").
        """
        if not value:
            raise ValueError("Missing date value")
        # Try ISO 8601; fallback to date-only
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            return datetime.strptime(value, "%Y-%m-%d").date()
