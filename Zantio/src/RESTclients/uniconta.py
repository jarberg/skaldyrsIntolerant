import os
from dataclasses import asdict

import requests
import json
from openpyxl.pivot.fields import Boolean

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

    def find_deptor(self, invoice):

        if invoice.customer.vatID is None:
            return None
        #print("vatID: "+str(invoice.customer.vatID))
        payload = [
                {
                    "PropertyName": "VatNumber",
                    "FilterValue": invoice.customer.vatID,
                    "Skip": 0,
                    "Take": 0,
                    "OrderBy": "true",
                    "OrderByDescending": "true"
                }
            ]

        for endpoint in ["DebtorClient", "DebtorClientUser", "DebtorTransClient"]:

            url = f"{self.base_url}/Query/Get/{endpoint}"  # adjust path to your ERP
            resp = self.session.post(url, json=payload)
            if not resp.ok:
                raise RuntimeError(f"ERP create_invoice failed: {resp.status_code} {resp.text}")
            data = resp.json()
            if len(data) > 0:
                break


        return data



    def create_invoice(self, invoice: CustomerInvoice, failedlist) -> str:
        """
        Create an invoice in your ERP system.
        Returns the ERP invoice ID/number.
        """
        erp_customer_id = invoice.customer.external_id
        deptor = self.find_deptor(invoice)

        if deptor is None or len(deptor) < 1:
            failedlist.append(invoice)
            return

        deptor = deptor[0]
        name = deptor.get("Name", "FAAILED")

        # Example JSON payload for a generic ERP.
        payload = {
            "Account": deptor.get("Account"),
            "Account Name": deptor.get("Account Name"),
            "YourRef": "API-ORDER-001",
            "invoice_date": invoice.period_end,
            "Simulate": "true"
        }


        url = f"{self.base_url}/Crud/Insert/DebtorOrderClient"  # adjust path to your ERP
        resp = self.session.post(url, json=payload)
        if not resp.ok:
            raise RuntimeError(f"ERP create_invoice failed: {resp.status_code} {resp.text}")
        data = resp.json()
        OrderNumber = str(data.get("OrderNumber") or data.get("invoiceNumber"))
        print(f"Created ERP invoice {OrderNumber} for customer {invoice.customer.name}")


        url = f"{self.base_url}/Crud/InsertList/DebtorOrderLineClient"  # adjust path to your ERP
        for categoryKey in invoice.categories:
            category = invoice.categories[categoryKey]
            jsonObject = []
            for catline in category.lines:
                catline.OrderNumber = OrderNumber
                print(asdict(catline))
                jsonObject.append(asdict(catline))

            resp = self.session.post(url, json=jsonObject )
            if not resp.ok:
                raise RuntimeError(f"ERP create_invoice failed: {resp.status_code} {resp.text}")
            data = resp.json()


        return OrderNumber
