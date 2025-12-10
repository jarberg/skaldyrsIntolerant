import io

from openpyxl import load_workbook

from reconcilliation.utils import recon_data

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