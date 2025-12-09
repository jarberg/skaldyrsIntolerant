
global DRY_RUN

import io

from openpyxl import load_workbook
from dotenv import load_dotenv

load_dotenv()

import util as util
from reconcilliation.utils import setupStreamletPage, recon_data
from RESTclients import cloudfactory as cf, uniconta as uc
from RESTclients.dataModels import (
    CustomerInvoice,
    CustomerInvoiceCategory,
    CustomerInvoiceCategoryLine_exclaimer,
    CustomerInvoiceCategoryLine_keepit,
    CustomerInvoice_Error,
)


def generate_correct_product_line(catName, record):
    if catName == "Exclaimer":
        line = CustomerInvoiceCategoryLine_exclaimer(
            Amount=record.get("Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Item Name", "Failed"),
            ItemNo=record.get("ItemNo", "Failed"),
            LicenseAgreementType=record.get("License Agreement Type", "Failed"),
            Offering=record.get("Offering", "Failed"),
            ProductFamily=record.get("Product Family", "Failed"),
            Quantity=record.get("Quantity", "Failed"),
            UnitPrice="",
        )
    elif catName in [
        "Keepit",
        "Impossible Cloud",
        "Acronis",
        "Dropbox",
        "Microsoft CSP (NCE)",
        "SPLA",
    ]:
        line = CustomerInvoiceCategoryLine_keepit(
            Amount=record.get("Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Item Name", "Failed"),
            ItemNo=record.get("ItemNo", "Failed"),
            LicenseAgreementType=record.get("License Agreement Type", "Failed"),
            Offering=record.get("Offering", "Failed"),
            ProductFamily=record.get("Product Family", "Failed"),
            Quantity=record.get("Quantity", "Failed"),
            UnitPrice="",
        )
    else:
        line = CustomerInvoiceCategoryLine_keepit(
            Amount=record.get("Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Item Name", "Failed"),
            ItemNo=record.get("ItemNo", "Failed"),
            LicenseAgreementType=record.get("License Agreement Type", "Failed"),
            Offering=record.get("Offering", "Failed"),
            ProductFamily=record.get("Product Family", "Failed"),
            Quantity=record.get("Quantity", "Failed"),
            UnitPrice="",
        )
    return line

def createUniconta(uniconta_client):
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

def get_headers(excel_bytes):
    wb = load_workbook(io.BytesIO(excel_bytes))
    ws = wb.active
    #if wb.active.title == "Usage" or wb.active.title == "Acronis Total":
       #ws = wb.worksheets[1]
    # else:
      #  ws = wb.active

    # header row
    header_row = next(ws.iter_rows(values_only=True))
    headers = [cell for cell in header_row]
    return headers, list(ws.iter_rows(min_row=2, values_only=True))

def get_id_keys(headers, data_rows, catKey):
    success = True
    id_key = None
    vat_key = None
    name_key = None

    if "Portal Customer Id" in headers:
        id_key = "Portal Customer Id"
        vat_key = "Portal Customer VAT"
        name_key = "Portal Customer Name"
    elif "Customer Id" in headers:
        # Acronis / Impossible Cloud style
        id_key = "Customer Id"
        vat_key = "Customer VAT" if "Customer VAT" in headers else None
        name_key = "Customer Name"
    else:
        success = False
        for row in data_rows:
            record = dict(zip(headers, row))

            try:
                amount_val = float(record.get("Amount", 0) or 0)
            except (TypeError, ValueError):
                amount_val = 0.0

            recon_data.total_amount_no_customerid += amount_val

            recon_data.no_customerid_rows.append(
                {
                    "Category": catKey,
                    "InvoicePeriodStart": record.get("Start Date", ""),
                    "InvoicePeriodEnd": record.get("End Date", ""),
                    "Item Name": record.get("Item Name", ""),
                    "ItemNo": record.get("ItemNo", ""),
                    "Quantity": record.get("Quantity", ""),
                    "Unit Price": record.get("Unit Price", ""),
                    "Amount": amount_val,
                    "Currency": record.get("Currency", ""),
                    "Customer Id": "",
                    "Customer Name (from Excel)": "",
                    "VAT (from Excel)": "",
                    "Note": "No customer id column in billing file",
                }
            )
    return id_key, vat_key, name_key, success


def main(*args, **kwargs):
    # DRY_RUN-flag (pt. ikke brugt til at slå Uniconta-kald fra)
    DRY_RUN = kwargs.get("DRY_RUN", "True").lower() == "true"

    util.get_latest_date()

    cloudFac_client = cf.CloudFactoryClient()
    uniconta_client = uc.UnicontaClient()

    print("Fetching customers from CloudFactory...")
    uniconta_client.customerDataBase = cloudFac_client.list_customers()

    invoices = cloudFac_client.fetch_latest_invoices()

    foundCatKeyDict = set()

    for invoice in invoices:
        for catKey in invoice.categories.keys():
            foundCatKeyDict.add(catKey)

            # load excel bytes
            excel_bytes = cloudFac_client.fetch_billing_excel(
                invoice.categories.get(catKey).excelLink
            )
            headers, data_rows = get_headers(excel_bytes)

            id_key, vat_key, name_key, success = get_id_keys(headers, data_rows, catKey)
            if not success:
                continue

            previousCustomerid = None

            for row in data_rows:
                record = dict(zip(headers, row))
                try:
                    amount_val = float(record.get("Amount", 0) or 0)
                except (TypeError, ValueError):
                    amount_val = 0.0

                raw_id = record.get(id_key)
                if not raw_id:
                    recon_data.add_no_customerID_row(amount_val, catKey, record, name_key, vat_key)
                    continue

                customerid = (
                    str(raw_id).replace("{", "").replace("}", "").lower()
                )

                vatID = record.get(vat_key, "NULL") if vat_key else "NULL"
                name = record.get(name_key, "NULL")

                # Build / reuse the CustomerInvoice / CustomerInvoice_Error
                customerinvoice = generate_customer_invoice(
                    previousCustomerid,
                    customerid,
                    vatID,
                    name,
                    record,
                    uniconta_client
                )

                category = customerinvoice.categories.get(catKey, None)
                if not category:
                    category = CustomerInvoiceCategory(
                        name=catKey,
                        lines=[],
                    )
                    customerinvoice.categories[catKey] = category

                line = generate_correct_product_line(catKey, record)
                category.lines.append(line)
                previousCustomerid = customerid

                recon_data.total_amount_all += amount_val


    createUniconta(uniconta_client)

    setupStreamletPage(foundCatKeyDict)

def generate_customer_invoice(
    previousCustomerid,
    customerid,
    vatID,
    name,
    record,
    uniconta_adapter,
):

    if (
        previousCustomerid != customerid
        and (customerid not in recon_data.invoiceCustomerdict.keys())
        and (customerid not in recon_data.failedCustomerlist.keys())
    ):
        potential_clients = list(
            (
                x
                for x in uniconta_adapter.customerDataBase
                if (x.id.lower() == customerid.lower())
            )
        )
        match len(potential_clients):
            case 0:
                customerInvoice = CustomerInvoice_Error(
                    customer=None,
                    reason="No match found for customer with name: "
                    + name
                    + " with vatid: "
                    + vatID,
                    categories={},
                )
                recon_data.failedCustomerlist[customerid] = customerInvoice
            case 1:
                customerInvoice = CustomerInvoice(
                    customer=potential_clients[0],
                    period_start=record.get("Start Date", "ERROR"),
                    period_end=record.get("End Date", "ERROR"),
                    categories={},
                )
                recon_data.invoiceCustomerdict[customerid] = customerInvoice
            case _:
                customerInvoice = CustomerInvoice_Error(
                    customer=None,
                    reason="to many matches found for customer with name: "
                    + name
                    + " with vatid: "
                    + vatID,
                    categories={},
                )
                recon_data.failedCustomerlist[customerid] = customerInvoice
    else:
        if customerid in recon_data.failedCustomerlist.keys():
            customerInvoice = recon_data.failedCustomerlist.get(customerid)
        else:
            customerInvoice = recon_data.invoiceCustomerdict.get(customerid)

    if not customerInvoice:
        customerInvoice = CustomerInvoice_Error(
            customer=None,
            reason="Base catched error. Customerid: "
            + customerid
            + " VatID: "
            + vatID
            + " Name: "
            + name
            + "",
            categories={},
        )
        recon_data.failedCustomerlist[customerid] = customerInvoice

    return customerInvoice


if __name__ == "__main__":
    main()
