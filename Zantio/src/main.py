global DRY_RUN

import io
from RESTclients.dataModels import CustomerInvoice, CustomerInvoiceCategory, CustomerInvoiceCategoryLine_exclaimer, \
    CustomerInvoiceCategoryLine_keepit, CustomerInvoice_Error
from openpyxl import load_workbook

import util as util
from RESTclients import cloudfactory as cf, uniconta as uc

def generate_correct_product_line(catName, record):
    line = None
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
            UnitPrice=record.get("Unit Price", "Failed"),
        )
    elif catName == "Keepit":
        line = CustomerInvoiceCategoryLine_keepit(
            Amount=record.get("Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Item Name", "Failed"),
            ItemNo=record.get("ItemNo", "Failed"),
            LicenseAgreementType=record.get("License Agreement Type", "Failed"),
            Offering=record.get("Offering", "Failed"),
            ProductFamily=record.get("Product Family", "Failed"),
            Quantity=record.get("Quantity", "Failed"),
            UnitPrice=record.get("Unit Price", "Failed"),
        )

    elif catName =="Impossible Cloud":
        line = CustomerInvoiceCategoryLine_keepit(
            Amount=record.get("Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Item Name", "Failed"),
            ItemNo=record.get("ItemNo", "Failed"),
            LicenseAgreementType=record.get("License Agreement Type", "Failed"),
            Offering=record.get("Offering", "Failed"),
            ProductFamily=record.get("Product Family", "Failed"),
            Quantity=record.get("Quantity", "Failed"),
            UnitPrice=record.get("Unit Price", "Failed"),
        )
    elif catName =="Acronis":
        line = CustomerInvoiceCategoryLine_keepit(
            Amount=record.get("Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Item Name", "Failed"),
            ItemNo=record.get("ItemNo", "Failed"),
            LicenseAgreementType=record.get("License Agreement Type", "Failed"),
            Offering=record.get("Offering", "Failed"),
            ProductFamily=record.get("Product Family", "Failed"),
            Quantity=record.get("Quantity", "Failed"),
            UnitPrice=record.get("Unit Price", "Failed"),
        )
    elif catName =="Dropbox":
        line = CustomerInvoiceCategoryLine_keepit(
            Amount=record.get("Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Item Name", "Failed"),
            ItemNo=record.get("ItemNo", "Failed"),
            LicenseAgreementType=record.get("License Agreement Type", "Failed"),
            Offering=record.get("Offering", "Failed"),
            ProductFamily=record.get("Product Family", "Failed"),
            Quantity=record.get("Quantity", "Failed"),
            UnitPrice=record.get("Unit Price", "Failed"),
        )
    elif catName =="Microsoft CSP (NCE)":
        line = CustomerInvoiceCategoryLine_keepit(
            Amount=record.get("Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Item Name", "Failed"),
            ItemNo=record.get("ItemNo", "Failed"),
            LicenseAgreementType=record.get("License Agreement Type", "Failed"),
            Offering=record.get("Offering", "Failed"),
            ProductFamily=record.get("Product Family", "Failed"),
            Quantity=record.get("Quantity", "Failed"),
            UnitPrice=record.get("Unit Price", "Failed"),
        )
    elif catName == "SPLA":
        line = CustomerInvoiceCategoryLine_keepit(
            Amount=record.get("Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Item Name", "Failed"),
            ItemNo=record.get("ItemNo", "Failed"),
            LicenseAgreementType=record.get("License Agreement Type", "Failed"),
            Offering=record.get("Offering", "Failed"),
            ProductFamily=record.get("Product Family", "Failed"),
            Quantity=record.get("Quantity", "Failed"),
            UnitPrice=record.get("Unit Price", "Failed"),
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
            UnitPrice=record.get("Unit Price", "Failed"),
        )
    return line

def print_invoices(invoiceCustomerdict):
    for invoice in invoiceCustomerdict.values():
        print(invoice.customer.name)
        for key in invoice.categories.keys():
            category = invoice.categories.get(key)
            print("   |_ " + key)
            for line in category.lines:
                print("         |_ itemName: " + line.ItemName)
                print("         |_ ProductFamily: " + line.ProductFamily)
                print("         |_ amount: " + str(line.Amount))
                print("         |_ quantity: " + str(line.Quantity))
                print("         |_ unitPrice: " + str(line.UnitPrice))
                print("         |")

        print("")


def main(*args, **kwargs):
    # Whether to run in "dry run" mode (show what would happen, but don't create uniconta invoices)
    DRY_RUN = kwargs.get("DRY_RUN", "True").lower() == "true"

    util.get_latest_date()

    cloudFac_client = cf.CloudFactoryClient()
    uniconta_client = uc.UnicontaAdapter()

    print("Fetching customers from CloudFactory...")
    uniconta_client.customerDataBase = cloudFac_client.list_customers()

    print(f"Found {len(uniconta_client.customerDataBase)} customers.")

    invoices = cloudFac_client.fetch_latest_invoices()
    invoiceCustomerdict = {}
    failedCustomerlist = {}

    foundCatKeyDict = set()

    for invoice in invoices:
        for catKey in invoice.categories.keys():
            foundCatKeyDict.add(catKey)
            # load excel bytes
            excel_bytes = cloudFac_client.fetch_billing_excel(invoice.categories.get(catKey).excelLink)
            wb = load_workbook(io.BytesIO(excel_bytes))
            ws = wb.active

            headers = [cell for cell in next(ws.iter_rows(values_only=True))]
            if headers.__contains__("Portal Customer Id"):
                previousCustomerid = None

                for row in ws.iter_rows(min_row=2, values_only=True):
                    record = dict(zip(headers, row))
                    customerid = record.get("Portal Customer Id").replace("{", "").replace("}", "").lower()
                    vatID = record.get("Portal Customer VAT", "NULL")
                    name = record.get("Portal Customer Name", "NULL")

                    customerinvoice = generate_customer_invoice(previousCustomerid, customerid,vatID, name, invoiceCustomerdict, record, uniconta_client, failedCustomerlist)

                    category_name = catKey
                    category = customerinvoice.categories.get(category_name, None)
                    if not category:
                        category = CustomerInvoiceCategory(
                            name=category_name,
                            lines = []
                        )
                        customerinvoice.categories[category_name] = category

                    line = generate_correct_product_line(category_name, record)
                    category.lines.append(line)
                    previousCustomerid = customerid

    failedList = []

    for customerInvoice in invoiceCustomerdict.values():
        uniconta_client.create_invoice(customerInvoice, failedList)

    for failed in failedList:
        print(failed)

    #for failed in failedCustomerlist.keys():
    #    print(failedCustomerlist[failed].reason)
    #    for category in failedCustomerlist.get(failed).categories:
    #        print("   "+category)
    #        for line in failedCustomerlist.get(failed).categories[category].lines:
    #            print("      "+line.ItemName  )
    #    print("")


def generate_customer_invoice(previousCustomerid, customerid, vatID, name, invoiceCustomerdict, record, uniconta_adapter, failedCustomerlist):

    error=True
    if previousCustomerid != customerid and (not customerid in invoiceCustomerdict.keys() and not customerid in failedCustomerlist.keys()):
        potential_clients = list(
            (x for x in uniconta_adapter.customerDataBase if (x.id.lower() == customerid.lower())))
        match len(potential_clients):
            case 0:
                customerinvoice = CustomerInvoice_Error(
                    customer = None,
                    reason = "No match found for customer with name: " + name + " with vatid: " + vatID,
                    categories = {}
                )
                failedCustomerlist[customerid] = customerinvoice
            case 1:
                customerinvoice = CustomerInvoice(
                    customer=potential_clients[0],
                    period_start=record.get("Start Date", "ERROR"),
                    period_end=record.get("End Date", "ERROR"),
                    categories={}
                )
                invoiceCustomerdict[customerid] = customerinvoice
            case _:
                customerinvoice = CustomerInvoice_Error(
                    customer=None,
                    reason="to many matches found for customer with name: " + name + " with vatid: " + vatID,
                    categories={}
                )
                failedCustomerlist[customerid] = customerinvoice
    else:
        if customerid in failedCustomerlist.keys():
            customerinvoice = failedCustomerlist.get(customerid)
        else:
            customerinvoice = invoiceCustomerdict.get(customerid)
    if not customerinvoice:
        customerinvoice = CustomerInvoice_Error(
            customer=None,
            reason="Base catched error. Customerid: " + customerid + " VatID: " + vatID + " Name: " + name + "",
            categories={}
        )
        failedCustomerlist[customerid] = customerinvoice

    return customerinvoice




if __name__ == "__main__":
    main()
