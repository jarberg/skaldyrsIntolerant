global DRY_RUN

from dotenv import load_dotenv

load_dotenv()

import io
import csv
from pathlib import Path

from RESTclients.dataModels import (
    CustomerInvoice,
    CustomerInvoiceCategory,
    CustomerInvoiceCategoryLine_exclaimer,
    CustomerInvoiceCategoryLine_keepit,
    CustomerInvoice_Error,
)
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

    elif catName == "Impossible Cloud":
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
    elif catName == "Acronis":
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
    elif catName == "Dropbox":
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
    elif catName == "Microsoft CSP (NCE)":
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


def export_failed_customers_csv(failedCustomerlist, output_path="failed_customers.csv"):
    """
    Export CloudFactory rows that could NOT be matched to a CloudFactory customer
    (i.e., entries stored in failedCustomerlist from generate_customer_invoice).
    """
    rows = []

    for customerid, customer_invoice in failedCustomerlist.items():
        reason = getattr(customer_invoice, "reason", "Unknown")

        # Compute total amount for this failed customer
        total_amount = 0.0
        for category in customer_invoice.categories.values():
            for line in category.lines:
                try:
                    total_amount += float(line.Amount or 0)
                except Exception:
                    pass

        customer_name = (
            customer_invoice.customer.name
            if customer_invoice.customer else "Unknown"
        )
        vat = (
            customer_invoice.customer.vatID
            if customer_invoice.customer else "Unknown"
        )

        rows.append({
            "Customer ID": customerid,
            "Customer Name": customer_name,
            "VAT": vat,
            "Reason": reason,
            "Total Amount (DKK)": total_amount,
        })

    if not rows:
        print("No failed CloudFactory customers – nothing to write to CSV.")
        return

    # Write CSV
    output_file = Path(output_path)
    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Failed customer CSV exported -> {output_file.resolve()}")


def export_missing_debtors_csv(failed_invoices, output_path="failed_debtors_uniconta.csv"):
    """
    Export customers for whom we could NOT find a debtor in Uniconta.
    This corresponds to the big 'No matching debtor in Uniconta' amount.
    """
    rows = []

    for inv in failed_invoices:
        cust = inv.customer
        if not cust:
            continue

        # Compute total amount for this invoice
        total_amount = 0.0
        for category in inv.categories.values():
            for line in category.lines:
                try:
                    total_amount += float(line.Amount or 0)
                except Exception:
                    pass

        rows.append({
            "Customer ID": cust.id,
            "Customer Name": cust.name,
            "VAT": cust.vatID,
            "Country": cust.countryCode,
            "Reason": "No matching debtor in Uniconta (find_deptor returned none)",
            "Total Amount (DKK)": total_amount,
        })

    if not rows:
        print("No missing debtors – all CustomerInvoices found a debtor in Uniconta.")
        return

    output_file = Path(output_path)
    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Missing debtors CSV exported -> {output_file.resolve()}")


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
    invoiceCustomerdict: dict[str, CustomerInvoice] = {}
    failedCustomerlist: dict[str, CustomerInvoice_Error] = {}

    foundCatKeyDict = set()

    # Reconciliation totals
    total_amount_all = 0.0          # all processed lines with some customer id
    total_amount_success = 0.0      # those that actually created Uniconta orders
    total_amount_failed = 0.0       # those that did not create orders

    for invoice in invoices:
        for catKey in invoice.categories.keys():
            foundCatKeyDict.add(catKey)

            # load excel bytes
            excel_bytes = cloudFac_client.fetch_billing_excel(
                invoice.categories.get(catKey).excelLink
            )
            wb = load_workbook(io.BytesIO(excel_bytes))
            ws = wb.active

            # header row
            header_row = next(ws.iter_rows(values_only=True))
            headers = [cell for cell in header_row]

            # --- Determine which columns hold customer id / vat / name ---
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
                print(
                    f"[DEBUG] Category '{catKey}' has no usable customer id column. Headers: {headers}"
                )
                continue

            # collect all data rows so we can both count and iterate
            data_rows = list(ws.iter_rows(min_row=2, values_only=True))
            print(
                f"[DEBUG] Category '{catKey}' contains {len(data_rows)} rows in Excel."
            )

            previousCustomerid = None

            for row in data_rows:
                record = dict(zip(headers, row))

                raw_id = record.get(id_key)
                if not raw_id:
                    # skip rows with no customer id at all
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
                    invoiceCustomerdict,
                    record,
                    uniconta_client,
                    failedCustomerlist,
                )

                # Create / get the category on that invoice
                category_name = catKey
                category = customerinvoice.categories.get(category_name, None)
                if not category:
                    category = CustomerInvoiceCategory(
                        name=category_name,
                        lines=[],
                    )
                    customerinvoice.categories[category_name] = category

                # Create the line from CloudFactory record
                line = generate_correct_product_line(category_name, record)
                category.lines.append(line)
                previousCustomerid = customerid

                # --- Reconciliation: accumulate total amount only ---
                amount_raw = record.get("Amount", 0) or 0
                try:
                    amount_val = float(amount_raw)
                except (TypeError, ValueError):
                    amount_val = 0.0

                total_amount_all += amount_val

    failedList: list[CustomerInvoice] = []

    # These will reflect what actually reached Uniconta
    total_amount_success = 0.0
    total_amount_failed = 0.0

    # Actually create invoices in Uniconta
    for customerInvoice in invoiceCustomerdict.values():
        before = len(failedList)
        uniconta_client.create_invoice(customerInvoice, failedList)
        after = len(failedList)

        # Sum the invoice amount from its lines
        inv_amount = 0.0
        for category in customerInvoice.categories.values():
            for line in category.lines:
                try:
                    inv_amount += float(line.Amount or 0)
                except (TypeError, ValueError):
                    pass

        if after == before:
            # No new failure added => this invoice was successfully posted
            total_amount_success += inv_amount
        else:
            # This invoice ended up in failedList
            total_amount_failed += inv_amount

    # Debug: which categories did we see at all?
    print("\n=== CloudFactory billing categories discovered ===")
    print(foundCatKeyDict)
    print("=================================================\n")

    # --- Reconciliation summary ---
    print("=== RECONCILIATION SUMMARY (ex. VAT) ===")
    print(f"Total CloudFactory per-customer amount processed : {total_amount_all:,.2f} DKK")
    print(f"  → Mapped to existing Uniconta debtors          : {total_amount_success:,.2f} DKK")
    print(f"  → No matching debtor in Uniconta (skipped)     : {total_amount_failed:,.2f} DKK")
    print(f"  Check (success + failed)                       : {(total_amount_success + total_amount_failed):,.2f} DKK")
    print("=========================================\n")

    # Print which invoices failed because no debtor was found (or similar)
    for failed in failedList:
        print(failed)

    # Export CloudFactory mapping failures (the small ~11k issue)
    if failedCustomerlist:
        export_failed_customers_csv(failedCustomerlist, "failed_customers.csv")
    else:
        print("No failed customers to export – all CloudFactory customers matched a customer record.")

    # Export Uniconta debtor failures (the big ~436k issue)
    if failedList:
        export_missing_debtors_csv(failedList, "failed_debtors_uniconta.csv")
    else:
        print("No failed Uniconta debtor matches to export.")

def generate_customer_invoice(
    previousCustomerid,
    customerid,
    vatID,
    name,
    invoiceCustomerdict,
    record,
    uniconta_adapter,
    failedCustomerlist,
):

    error = True
    if (
        previousCustomerid != customerid
        and (customerid not in invoiceCustomerdict.keys())
        and (customerid not in failedCustomerlist.keys())
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
                customerinvoice = CustomerInvoice_Error(
                    customer=None,
                    reason="No match found for customer with name: "
                    + name
                    + " with vatid: "
                    + vatID,
                    categories={},
                )
                failedCustomerlist[customerid] = customerinvoice
            case 1:
                customerinvoice = CustomerInvoice(
                    customer=potential_clients[0],
                    period_start=record.get("Start Date", "ERROR"),
                    period_end=record.get("End Date", "ERROR"),
                    categories={},
                )
                invoiceCustomerdict[customerid] = customerinvoice
            case _:
                customerinvoice = CustomerInvoice_Error(
                    customer=None,
                    reason="to many matches found for customer with name: "
                    + name
                    + " with vatid: "
                    + vatID,
                    categories={},
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
            reason="Base catched error. Customerid: "
            + customerid
            + " VatID: "
            + vatID
            + " Name: "
            + name
            + "",
            categories={},
        )
        failedCustomerlist[customerid] = customerinvoice

    return customerinvoice


if __name__ == "__main__":
    main()
