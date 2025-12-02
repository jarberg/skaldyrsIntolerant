global DRY_RUN

import io
from RESTclients.dataModels import CustomerInvoice
from openpyxl import load_workbook

import util as util
from RESTclients import cloudfactory as cf, uniconta as uc
from adapters import pandas as pda

def main(*args, **kwargs):
    # Whether to run in "dry run" mode (show what would happen, but don't create uniconta invoices)
    DRY_RUN = kwargs.get("DRY_RUN", "True").lower() == "true"

    util.get_latest_date()

    cloudFac_client = cf.CloudFactoryClient()
    uniconta_adapter = uc.UnicontaAdapter()

    print("Fetching customers from CloudFactory...")
    uniconta_adapter.customerDataBase = cloudFac_client.list_customers()

    pda.main(cloudFac_client)

    for customerinvoice in uniconta_adapter.customerDataBase :
        print(customerinvoice.id+":"+ customerinvoice.vatID,":",customerinvoice.name)

    invoices = cloudFac_client.fetch_latest_invoices()
    Customerdict = {}

    for invoice in invoices:
        print(invoice.endDate)
        for catKey in invoice.categories.keys():
            print("   "+invoice.categories.get(catKey).name+"   " + invoice.categories.get(catKey).excelLink)
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

                    if previousCustomerid != None:
                        if previousCustomerid != customerid:
                            print(f"Found new customer: {customerid}")

                    if customerid in Customerdict:
                        customerinvoice = Customerdict.get(customerid)

                    else:
                        potential_clients = list((x for x in uniconta_adapter.customerDataBase if (x.id.lower() == customerid.lower())))
                        match len(potential_clients):
                            case 0:
                                print(customerid, vatID, "No match found for customer with name: "+name + " with vatid: "+vatID )
                                continue
                            case 1:
                                customerinvoice = CustomerInvoice(
                                    customer =  potential_clients[0],
                                    period_start = record.get("Start Date", "ERROR"),
                                    period_end= record.get("End Date", "ERROR"),
                                    categories=[]
                                )
                                Customerdict[customerid] = customerinvoice
                            case _:
                                print("other")
                                raise Exception("too many match found for customer")

                    previousCustomerid = customerid
                    #print(list(((record[x] for x in headers))))

    for key in Customerdict:
        print(key, Customerdict.get(key))

    print(f"Found {len(uniconta_adapter.customerDataBase)} customers.")


if __name__ == "__main__":
    main()
