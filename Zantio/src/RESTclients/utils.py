from RESTclients.CloudFactory.cloudfactory import generate_correct_product_line
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
    errors = 0

    for invoice in invoices:
        for catKey in invoice.categories.keys():
            foundCatKeyDict.add(catKey)

            excel_bytes = cloudFac_client.fetch_billing_excel(
                invoice.categories.get(catKey).excelLink
            )
            data_dict = convert_excel_to_dict(excel_bytes)

            id_key, vat_key, name_key, success = get_id_keys(data_dict, catKey)
            if not success:
                errors+=1
                continue

            previousCustomerid = None

            for record in data_dict:
                raw_id = record.get(id_key)
                if not raw_id:
                    recon_data.add_no_customerID_row(catKey, record, name_key, vat_key)
                    errors += 1
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

                recon_data.add_to_total_amount(record)
    return errors