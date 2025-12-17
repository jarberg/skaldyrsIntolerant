from RESTclients.Adapters.CloudFactoryToPython import generate_correct_product_line
from RESTclients.dataModels import CustomerInvoice_Error, CustomerInvoice, CustomerInvoiceCategory
from adapters.excel import convert_excel_to_dict, get_id_keys
from reconcilliation.utils import recon_data


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
        and (customerid not in recon_data.invoice_customer_dict.keys())
        and (customerid not in recon_data.failed_customer_list.keys())
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
                recon_data.failed_customer_list[customerid] = customerInvoice
            case 1:
                customerInvoice = CustomerInvoice(
                    customer=potential_clients[0],
                    period_start=record.get("Start Date", "ERROR"),
                    period_end=record.get("End Date", "ERROR"),
                    categories={},
                )
                recon_data.invoice_customer_dict[customerid] = customerInvoice
            case _:
                customerInvoice = CustomerInvoice_Error(
                    customer=None,
                    reason="to many matches found for customer with name: "
                    + name
                    + " with vatid: "
                    + vatID,
                    categories={},
                )
                recon_data.failed_customer_list[customerid] = customerInvoice
    else:
        if customerid in recon_data.failed_customer_list.keys():
            customerInvoice = recon_data.failed_customer_list.get(customerid)
        else:
            customerInvoice = recon_data.invoice_customer_dict.get(customerid)

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
        recon_data.failed_customer_list[customerid] = customerInvoice

    return customerInvoice

def generate_invoice_category(invoice, catName):
    category = invoice.categories.get(catName, None)
    if not category:
        category = CustomerInvoiceCategory(
            name=catName,
            lines=[],
        )
        invoice.categories[catName] = category
    return category

def generate_invoices_for_uniconta(cloudFac_client, uniconta_client, invoices, foundCatKeyDict):
    errors = 0
    #preload excel data structures
    for invoice in invoices:
        for catKey in invoice.categories.keys():
            foundCatKeyDict.add(catKey)

            excel_bytes = cloudFac_client.fetch_billing_excel(
                invoice.categories.get(catKey).excelLink
            )
            invoice_rows = convert_excel_to_dict(excel_bytes)
            invoice.categories.get(catKey).excelLink = invoice_rows
            id_key, vat_key, name_key, success = get_id_keys(invoice_rows)
            if not success:
                for record in invoice_rows:
                    recon_data.add_failed_customer(catKey, record)
                invoice.categories[catKey] = None
                errors+=1
                continue

            invoice.categories.get(catKey).idKey = id_key
            invoice.categories.get(catKey).vatKey = vat_key
            invoice.categories.get(catKey).nameKey = name_key

    #remove all categories that failed to get correct keys for important headers
    for invoice in invoices:
        invoice.categories = {k: v for k, v in invoice.categories.items() if v is not None}

    for invoice in invoices:
        for catKey in invoice.categories.keys():
            invoice_rows = invoice.categories.get(catKey).excelLink
            id_key=invoice.categories.get(catKey).idKey
            vat_key=invoice.categories.get(catKey).vatKey
            name_key=invoice.categories.get(catKey).nameKey

            previous_customer_id = None

            for row in invoice_rows:
                raw_id = row.get(id_key)

                customer_id = str(raw_id).replace("{", "").replace("}", "").lower()
                vatID = row.get(vat_key, "NULL") if vat_key else "NULL"
                name = row.get(name_key, "NULL")

                # Build / reuse the CustomerInvoice / CustomerInvoice_Error
                customer_invoice = generate_customer_invoice(
                    previous_customer_id,
                    customer_id,
                    vatID,
                    name,
                    row,
                    uniconta_client
                )

                category = generate_invoice_category(customer_invoice, catKey)
                line = generate_correct_product_line(catKey, row)

                #remove all zero amount entries  and merge identical entries
                if not (abs(line.Amount) == 0.0 and abs(line.Quantity) == 0.0):
                    addtolist = True
                    for catLine in category.lines:
                        if catLine.can_merge(line):
                            catLine += line
                            addtolist = False
                            break
                    if addtolist:
                        category.lines.append(line)

                    previous_customer_id = customer_id

                    recon_data.add_to_total_amount(row)

    return errors

