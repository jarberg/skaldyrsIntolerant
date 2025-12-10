from RESTclients.CloudFactory.cloudfactory import generate_correct_product_line
from RESTclients.dataModels import CustomerInvoice_Error, CustomerInvoice, CustomerInvoiceCategory
from adapters.excel import get_headers, get_id_keys
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


def generate_invoice(cloudFac_client, uniconta_client, invoices, foundCatKeyDict):
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