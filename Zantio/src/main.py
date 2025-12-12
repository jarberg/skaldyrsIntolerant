from util import format_str_with_color

global DRY_RUN
from dotenv import load_dotenv
load_dotenv()

from reconcilliation.utils import setupStreamletPage, recon_data
from RESTclients.Uniconta import uniconta as uc
from RESTclients.CloudFactory import cloudfactory as cf
from RESTclients.utils import generate_invoices_for_uniconta



def main(*args, **kwargs):
    DRY_RUN = kwargs.get("DRY_RUN", "True").lower() == "true"

    recon_data.reset()

    cloudFac_client = cf.CloudFactoryClient()
    uniconta_client = uc.UnicontaClient()

    print(format_str_with_color("Fetching customers from CloudFactory...", "blue"))

    uniconta_client.customerDataBase = cloudFac_client.list_customers()

    print(format_str_with_color(f"Found {len(uniconta_client.customerDataBase)} Cloudfactory Customers", "orange"))
    print(" ")

    print(format_str_with_color(f"Fetching latest invoice from CloudFactory...", "blue"))

    invoices, success = cloudFac_client.fetch_latest_invoices()

    if success: print(format_str_with_color(f"Found {len(invoices)} invoices", "orange"))
    else: print(format_str_with_color("No invoices found","red"))
    print(" ")
    foundCatKeyDict = set()

    print(format_str_with_color("Generating invoices...", "blue"))

    errors = generate_invoices_for_uniconta(cloudFac_client, uniconta_client, invoices, foundCatKeyDict)

    if errors > 0: print(format_str_with_color(f"Generated invoices with {errors} errors", "red"))
    else: print(format_str_with_color(f"Generated invoices with {errors} errors", "blue"))
    print(" ")

    print(format_str_with_color("Creating uniconta orders with lines...", "blue"))
    errorSet = dict()

    for customerInvoice in recon_data.invoice_customer_dict.values():
        error = uniconta_client.create_uniconta_order_with_lines(customerInvoice)
        if error:
            val = errorSet.get(error, 0)
            errorSet[error] = val + 1

    if len(errorSet.keys()) > 0: [print(format_str_with_color(f"Found {errorSet[x]} errors for error:Type {x}", "red"))for x in errorSet.keys()]
    else: print(format_str_with_color("No errors found", "green"))
    print(" ")

    print(format_str_with_color("Setup StreamletPage...", "blue"))
    setupStreamletPage(foundCatKeyDict)
