global DRY_RUN
from dotenv import load_dotenv
load_dotenv()

from reconcilliation.utils import setupStreamletPage, recon_data
from RESTclients.Uniconta import uniconta as uc
from RESTclients.CloudFactory import cloudfactory as cf
from RESTclients.utils import generate_invoice

def format_str_with_color(str, color):
    if color == "red": return f"\033[{31}m{str}\033[0m"
    if color == "green": return f"\033[{32}m{str}\033[0m"
    if color == "yellow":return f"\033[{33}m{str}\033[0m"
    if color == "blue": return f"\033[{34}m{str}\033[0m"
    if color == "orange": return f"\033[38;2;255;140;0m{str}\033[0m"
    return str

def main(*args, **kwargs):
    DRY_RUN = kwargs.get("DRY_RUN", "True").lower() == "true"

    cloudFac_client = cf.CloudFactoryClient()
    uniconta_client = uc.UnicontaClient()

    print(format_str_with_color("Fetching customers from CloudFactory...", "blue"))
    uniconta_client.customerDataBase = cloudFac_client.list_customers()
    print(format_str_with_color(f"Found {len(uniconta_client.customerDataBase )} Cloudfactory Customers", "orange"))
    print(" ")

    print(format_str_with_color(f"Fetching latest invoice from CloudFactory...", "blue"))
    invoices, success = cloudFac_client.fetch_latest_invoices()
    if success: print(format_str_with_color(f"Found {len(invoices)} invoices", "orange"))
    else: print(format_str_with_color("No invoices found","red"))
    print(" ")
    foundCatKeyDict = set()

    print("\033[34mGenerating invoices...\033[0m")
    errors = generate_invoice(cloudFac_client, uniconta_client, invoices, foundCatKeyDict)
    if errors > 0: print(format_str_with_color(f"Generated invoices with {errors} errors", "red"))
    else: print(format_str_with_color(f"Generated invoices with {errors} errors", "blue"))
    print(" ")

    print(format_str_with_color("Creating uniconta orders with lines...", "blue"))
    errorSet = dict()
    for customerInvoice in recon_data.invoiceCustomerdict.values():
        error = uniconta_client.create_uniconta_order_with_lines(customerInvoice)
        if error:
            val = errorSet.get(error, 0)
            errorSet[error] = val + 1

    if len(errorSet.keys()) > 0: [print(f"\033[31mFound {errorSet[x]} errors for error:Type {x}\033[0m")for x in errorSet.keys()]
    else: print("\033[32mNo errors found\033[0m")
    print(" ")

    print("Setup StreamletPage...")
    setupStreamletPage(foundCatKeyDict)



if __name__ == "__main__":
    main()
