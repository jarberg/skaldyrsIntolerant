global DRY_RUN
from dotenv import load_dotenv
load_dotenv()

from reconcilliation.utils import setupStreamletPage, recon_data
from RESTclients.Uniconta import uniconta as uc
from RESTclients.Uniconta.uniconta import createUnicontaOrdersWithLines
from RESTclients.CloudFactory import cloudfactory as cf
from RESTclients.utils import generate_invoice


def main(*args, **kwargs):
    DRY_RUN = kwargs.get("DRY_RUN", "True").lower() == "true"

    cloudFac_client = cf.CloudFactoryClient()
    uniconta_client = uc.UnicontaClient()

    print("Fetching customers from CloudFactory...")
    uniconta_client.customerDataBase = cloudFac_client.list_customers()

    print("Fetching latest invoice from CloudFactory...")
    invoices, success = cloudFac_client.fetch_latest_invoices()
    if success: print(f"Found {len(invoices)} invoices")
    else: print("No invoices found")

    foundCatKeyDict = set()

    print("Generating invoices...")
    generate_invoice(cloudFac_client, uniconta_client, invoices, foundCatKeyDict)

    print("Creating uniconta orders with lines...")
    createUnicontaOrdersWithLines(uniconta_client)

    print("Setup StreamletPage...")
    setupStreamletPage(foundCatKeyDict)



if __name__ == "__main__":
    main()
