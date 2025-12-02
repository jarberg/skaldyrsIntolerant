import os
import requests

from RESTclients.dataModels import CustomerInvoice

global DRY_RUN

class UnicontaAdapter:

    customerDataBase: list

    def __init__(self) -> None:

        self.base_url = os.getenv("ERP_BASE_URL", "https://erp.example.com/api")
        self.api_token = os.getenv("ERP_API_TOKEN")
        self.session = requests.Session()
        if self.api_token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            })


    def create_invoice(self, invoice: CustomerInvoice) -> str:
        """
        Create an invoice in your ERP system.
        Returns the ERP invoice ID/number.
        """
        erp_customer_id = invoice.customer.external_id

        # Example JSON payload for a generic ERP.
        payload = {
            "customer_id": erp_customer_id,
            "invoice_date": invoice.period_end.isoformat(),
            "due_date": (invoice.period_end.replace(day=invoice.period_end.day)  # adjust due date logic as needed
                         .isoformat()),
            "reference": f"CloudFactory services {invoice.period_start:%Y-%m}",
            "lines": [
                {
                    "description": line.description,
                    "quantity": line.quantity,
                    "unit_price": line.unit_price,
                    "total": line.total,
                    "sku": line.sku,
                }
                for line in invoice.lines
            ],
        }

        if DRY_RUN:
            print(f"[DRY RUN] Would POST invoice payload to ERP:\n{payload}\n")
            return "DRY_RUN_INVOICE_ID"

        url = f"{self.base_url}/invoices"  # adjust path to your ERP
        resp = self.session.post(url, json=payload)
        if not resp.ok:
            raise RuntimeError(f"ERP create_invoice failed: {resp.status_code} {resp.text}")
        data = resp.json()
        invoice_id = str(data.get("id") or data.get("invoiceNumber"))
        print(f"Created ERP invoice {invoice_id} for customer {invoice.customer.name}")
        return invoice_id
