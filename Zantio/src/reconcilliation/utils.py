
import csv
import json
from pathlib import Path

from RESTclients.dataModels import CustomerInvoice, CustomerInvoice_Error

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class recon_data:
    total_failed_cf = None
    total_amount_all = 0.0
    total_amount_success = 0.0
    total_amount_failed = 0.0
    total_amount_no_customerid = 0.0
    success_rows = []
    no_customerid_rows = []
    failedList = []
    invoiceCustomerdict: dict[str, CustomerInvoice] = {}
    failedCustomerlist: dict[str, CustomerInvoice_Error] = {}

    @classmethod
    def add_failed_customer(cls, catKey, record):

        try:
            amount_val = float(record.get("Amount", 0) or 0)
        except (TypeError, ValueError):
            amount_val = 0.0

        cls.total_amount_no_customerid += amount_val
        cls.no_customerid_rows.append(
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

    @classmethod
    def add_to_total_amount(cls, record):
        try:
            amount_val = float(record.get("Amount", 0) or 0)
        except (TypeError, ValueError):
            amount_val = 0.0
        recon_data.total_amount_all += amount_val

    @classmethod
    def add_no_customerID_row(cls, amount_val, catKey, record, name_key="", vat_key=""):
        try:
            amount_val = float(record.get("Amount", 0) or 0)
        except (TypeError, ValueError):
            amount_val = 0.0

        cls.total_amount_no_customerid += amount_val  # Ingen Customer Id i række kan ikke tildele til kunde
        cls.no_customerid_rows.append(
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
                "Customer Name (from Excel)": record.get(name_key, "") if 'name_key' in locals() else "",
                "VAT (from Excel)": record.get(vat_key, "") if 'vat_key' in locals() and vat_key else "",
                "Note": "Row has id column but Customer Id is empty",
            }
        )

def report_successOrFailure(customerInvoice, noNewfailures):
    # Sum invoice amount: ren Amount (CloudFactory-beløb)
    inv_amount = 0.0
    for category in customerInvoice.categories.values():
        for line in category.lines:
            try:
                inv_amount += float(line.Amount or 0)
            except (TypeError, ValueError):
                pass

    if noNewfailures:
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


def compute_line_total(line) -> float:
    """
    POTENTIEL hjælp: beløb = Quantity × UnitPrice, fallback til Amount.
    Pt. bruger vi konsekvent Amount til alle summeringer, da Amount er
    det økonomisk korrekte tal (tidsbaserede licenser m.m.).
    """
    try:
        qty = float(getattr(line, "Quantity", 0) or 0)
        price = float(getattr(line, "UnitPrice", 0) or 0)
        total = qty * price
        if total == 0 and getattr(line, "Amount", None) not in (None, "", 0):
            total = float(line.Amount or 0)
        return total
    except Exception:
        return 0.0

def export_failed_customers_csv(failedCustomerlist, output_path: Path) -> float:
    """
    CloudFactory-rækker der IKKE kunne matches til en CloudFactory-kunde.
    Beløb beregnes som Amount (CloudFactory-beløb).
    Returnerer totalbeløb.
    """
    rows = []
    total_failed = 0.0

    for customerid, customer_invoice in failedCustomerlist.items():
        reason = getattr(customer_invoice, "reason", "Unknown")

        total_amount = 0.0
        for category in customer_invoice.categories.values():
            for line in category.lines:
                try:
                    total_amount += float(line.Amount or 0)
                except Exception:
                    pass

        total_failed += total_amount

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
        return 0.0

    output_file = Path(output_path)
    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Failed customer CSV exported -> {output_file.resolve()}")
    return total_failed

def export_missing_debtors_csv(failed_invoices, output_path: Path) -> float:
    """
    Kunder hvor vi IKKE fandt en debitor i Uniconta.
    Beløb beregnes som Amount.
    Returnerer totalbeløb.
    """
    rows = []
    total_failed = 0.0

    for inv in failed_invoices:
        cust = inv.customer
        if not cust:
            continue

        total_amount = 0.0
        for category in inv.categories.values():
            for line in category.lines:
                try:
                    total_amount += float(line.Amount or 0)
                except Exception:
                    pass

        total_failed += total_amount

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
        return 0.0

    output_file = Path(output_path)
    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Missing debtors CSV exported -> {output_file.resolve()}")
    return total_failed

def export_success_invoices_csv(success_rows, output_path: Path) -> float:
    """
    Kunder hvor der blev oprettet en ordre i Uniconta.
    Rækkerne skal allerede indeholde 'Total Amount (DKK)' baseret på Amount.
    """
    if not success_rows:
        print("No successful invoices to export.")
        return 0.0

    total_success = sum(r.get("Total Amount (DKK)", 0.0) for r in success_rows)

    output_file = Path(output_path)
    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=success_rows[0].keys())
        writer.writeheader()
        writer.writerows(success_rows)

    print(f"Success invoices CSV exported -> {output_file.resolve()}")
    return total_success

def export_no_customerid_csv(no_id_rows, output_path: Path) -> float:
    """
    Linjer i billing-Excel uden Customer Id (enten mangler id-kolonne
    helt eller feltet er tomt). Beløb = Amount.
    Returnerer totalbeløbet.
    """
    if not no_id_rows:
        print("No 'no customer id' rows – nothing to write to CSV.")
        return 0.0

    total = 0.0
    for r in no_id_rows:
        try:
            total += float(r.get("Amount", 0.0) or 0.0)
        except Exception:
            pass

    output_file = Path(output_path)
    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=no_id_rows[0].keys())
        writer.writeheader()
        writer.writerows(no_id_rows)

    print(f"No-customer-id CSV exported -> {output_file.resolve()}")
    return total

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

def setupStreamletPage(foundCatKeyDict):
    # ------------------------------------------------------------------
    # Export CSVs for Streamlit / reporting
    # ------------------------------------------------------------------
    # 1) Successful invoices
    success_csv_path = OUTPUT_DIR / "success_invoices.csv"
    total_success_csv = export_success_invoices_csv(recon_data.success_rows, success_csv_path)

    # 2) CloudFactory mapping failures (failedCustomerlist)
    failed_cf_csv_path = OUTPUT_DIR / "failed_customers.csv"
    total_failed_cf = export_failed_customers_csv(recon_data.failedCustomerlist, failed_cf_csv_path)

    # 3) Uniconta debtor failures (failedList)
    failed_debtors_csv_path = OUTPUT_DIR / "failed_debtors_uniconta.csv"
    total_failed_debtors_csv = export_missing_debtors_csv(recon_data.failedList, failed_debtors_csv_path)

    # 4) No customer id lines
    no_customerid_csv_path = OUTPUT_DIR / "no_customerid_lines.csv"
    total_no_customerid_csv = export_no_customerid_csv(recon_data.no_customerid_rows, no_customerid_csv_path)

    # Debug: which categories did we see at all?
    print("\n=== CloudFactory billing categories discovered ===")
    print(foundCatKeyDict)
    print("=================================================\n")

    # --- Reconciliation summary (console) ---
    print("=== RECONCILIATION SUMMARY (ex. VAT) ===")
    print(f"Total CloudFactory per-customer amount processed         : {recon_data.total_amount_all+recon_data.total_amount_no_customerid:,.2f} DKK")
    print(f"  -> Mapped to existing Uniconta debtors                  : {recon_data.total_amount_success:,.2f} DKK")
    print(f"  -> No matching debtor in Uniconta (skipped)             : {recon_data.total_amount_failed:,.2f} DKK")
    print(f"  -> No matching CloudFactory customer (failed mapping)   : {total_failed_cf:,.2f} DKK")
    print(f"  -> Lines with NO customer id in billing file            : {recon_data.total_amount_no_customerid:,.2f} DKK")
    print(
        "Check (success + failed_debtors + failed_cf_customers)   : "
        f"{(recon_data.total_amount_success + recon_data.total_amount_failed + total_failed_cf):,.2f} DKK"
    )
    print(
        "Invoice header total (per-customer + no-id)              : "
        f"{(recon_data.total_amount_all + recon_data.total_amount_no_customerid):,.2f} DKK"
    )
    print("=========================================\n")

    for failed in recon_data.failedList:
        print(failed)

    # ------------------------------------------------------------------
    # Write reconciliation JSON for Streamlit
    # ------------------------------------------------------------------
    reconciliation = {
        "total_cloudfactory_amount": round(recon_data.total_amount_all, 2),
        "total_success_amount": round(recon_data.total_amount_success, 2),
        "total_failed_debtors_amount": round(recon_data.total_amount_failed, 2),
        "total_failed_cloudfactory_customers_amount": round(total_failed_cf, 2),
        "total_no_customerid_amount": round(recon_data.total_amount_no_customerid, 2),
        "success_csv": str(success_csv_path),
        "failed_customers_csv": str(failed_cf_csv_path),
        "failed_debtors_csv": str(failed_debtors_csv_path),
        "no_customerid_csv": str(no_customerid_csv_path),
        "calculation_notes_da": {
            "cloudfactory_total": (
                "CloudFactory totalen (per kunde) er baseret på feltet 'Amount' i "
                "billing-Excel (sum pr. kunde med gyldigt kunde-id, ekskl. moms)."
            ),
            "booked_to_debtors": (
                "'Bogført mod Uniconta-debitorer' er summen af CloudFactory 'Amount' "
                "for alle fakturaer, hvor der blev oprettet en ordre i Uniconta."
            ),
            "missing_debtors": (
                "'Ingen debitor i Uniconta' er summen af CloudFactory 'Amount' "
                "for fakturaer, hvor vi ikke kunne finde en debitor i Uniconta."
            ),
            "missing_cf_customers": (
                "'Ingen kundematch i CloudFactory' er summen af CloudFactory 'Amount' "
                "for linjer, hvor vi ikke kunne matche en CloudFactory-kunde (kunde-fejl)."
            ),
            "no_customerid": (
                "‘Linjer uden Customer Id’ er beløb fra billing-Excel (Amount), "
                "hvor der enten ikke findes nogen kunde-id-kolonne overhovedet, "
                "eller hvor Customer Id-feltet er tomt. De kan ikke kobles til en debitor, "
                "men er vigtige for den samlede fakturasum (fx enkelte Acronis-linjer)."
            ),
        },
    }

    recon_path = OUTPUT_DIR / "reconciliation_summary.json"
    with recon_path.open("w", encoding="utf-8") as f:
        json.dump(reconciliation, f, indent=2, ensure_ascii=False)

    print(f"Reconciliation JSON exported -> {recon_path.resolve()}")
