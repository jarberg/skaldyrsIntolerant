from datetime import datetime
from math import copysign

from RESTclients.dataModels import CustomerInvoiceCategoryLineBase


def generate_correct_product_line(catName, record, startDate, endDate):
    if catName == "Exclaimer":
        start = datetime.strptime(record.get("Start Date", "Failed"), "%d-%m-%y").date()
        end = datetime.strptime(record.get("End Date", "Failed"), "%d-%m-%y").date()
        line = CustomerInvoiceCategoryLineBase(
            Amount=record.get("Retail Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Item Name", "Exclaimer Failed"),
            ItemNo=record.get("Item No", "Failed"),
            Units="stk",
            CustomerName = record.get("Portal Customer Name"),
            ProductFamily=record.get("Subscription Name", "Failed"),
            Quantity=float(record.get("Quantity", 0.0)),
            UnitPrice=record.get("Unit Price", "Failed"),
            PeriodStart=start,
            PeriodEnd=end,
        )
    elif catName == "SPLA":
        line = CustomerInvoiceCategoryLineBase(
            Amount=record.get("Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Item Name", "SPLA Failed"),
            ItemNo=record.get("Item No", "Failed"),
            Units="stk",
            CustomerName=record.get("Portal Customer Name"),
            ProductFamily=record.get("Product Family", "Failed"),
            Quantity=float(record.get("Quantity", 0.0)),
            UnitPrice=record.get("Unit Price", "Failed"),
            PeriodStart=startDate,
            PeriodEnd=endDate
        )
    elif catName == "Microsoft CSP (NCE)":
        start = datetime.strptime(record.get("Start Date", "Failed"), "%d-%m-%y").date()
        end = datetime.strptime(record.get("End Date", "Failed"), "%d-%m-%y").date()
        line = CustomerInvoiceCategoryLineBase(
            Amount=record.get("Retail Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Nickname", "CSP Failed"),
            ItemNo=record.get("Item No", "Failed"),
            Units="stk",
            CustomerName=record.get("Portal Customer Name"),
            ProductFamily=record.get("Description", "Failed"),
            Quantity=float(record.get("Quantity", 0.0)),
            UnitPrice=record.get("Unit Price", "Failed"),
            PeriodStart=start,
            PeriodEnd=end
        )
    elif catName == "Keepit":
        start = datetime.strptime(record.get("Start Date", "Failed"), "%d-%m-%y").date()
        end = datetime.strptime(record.get("End Date", "Failed"), "%d-%m-%y").date()
        line = CustomerInvoiceCategoryLineBase(
            Amount=record.get("Retail Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Item Name", "Keepit Failed"),
            ItemNo=record.get("Item No", "Failed"),
            Units="stk",
            CustomerName=record.get("Portal Customer Name"),
            ProductFamily=record.get("Connector", "Failed"),
            Quantity=float(record.get("Quantity", 0.0)),
            UnitPrice=record.get("Unit Price", "Failed"),
            PeriodStart=start,
            PeriodEnd=end
        )
    elif catName == "Acronis":
        start = datetime.strptime(record.get("Start Date", "Failed"), "%d-%m-%y").date()
        end = datetime.strptime(record.get("End Date", "Failed"), "%d-%m-%y").date()
        line = CustomerInvoiceCategoryLineBase(
            Amount=record.get("Retail Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Description", "Acronis Failed"),
            ItemNo=record.get("Item No", "Failed"),
            Units=record.get("Unit", "Failed"),
            CustomerName=record.get("Portal Customer Name"),
            ProductFamily=record.get("Description", "Failed"),
            Quantity=float(record.get("Quantity", 0.0)),
            UnitPrice=record.get("Unit Price", "Failed"),
            PeriodStart=start,
            PeriodEnd=end
        )
    elif catName == "Dropbox":
        line = CustomerInvoiceCategoryLineBase(
            Amount=record.get("Retail Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Description", "Dropbox Failed"),
            ItemNo=record.get("Item No", "Failed"),
            Units="stk",
            CustomerName=record.get("Portal Customer Name"),
            ProductFamily="Dropbox",
            Quantity=float(record.get("License Quantity", 0.0)),
            UnitPrice=record.get("Unit Price", "Failed"),
            PeriodStart=startDate,
            PeriodEnd=endDate
        )
    elif catName == "Impossible Cloud":
        line = CustomerInvoiceCategoryLineBase(
            Amount=float(record.get("Quantity", 0.0))*50,
            Currency=record.get("Currency", "Failed"),
            ItemName="cloud service",
            ItemNo=record.get("Item No", "Failed"),
            Units="stk",
            CustomerName=record.get("Portal Customer Name"),
            ProductFamily="cloud service",
            Quantity=float(record.get("Quantity", 0.0)),
            UnitPrice=50,
            PeriodStart=startDate,
            PeriodEnd=endDate
        )
    elif catName == "Microsoft NCE (Azure)":
        line = CustomerInvoiceCategoryLineBase(
            Amount=record.get("Retail Amount", 0.0),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Description", "Azure Failed"),
            ItemNo=record.get("Product Id", "Failed"),
            Units="stk",
            CustomerName=record.get("Portal Customer Name"),
            ProductFamily=record.get("Product Group"),
            Quantity=float(record.get("Quantity", 0.0)),
            UnitPrice=record.get("Unit Price", "Failed"),
            PeriodStart=startDate,
            PeriodEnd=endDate
        )
    else:
        start = datetime.strptime(record.get("Billing Start Date", "Failed"), "%d-%m-%y").date()
        line = CustomerInvoiceCategoryLineBase(
            Amount=float(record.get("Amount", 0.0)),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Description", "else Failed"),
            ItemNo=record.get("Item No", "Failed"),
            Units="stk",
            CustomerName=record.get("Portal Customer Name"),
            ProductFamily="Dropbox",
            Quantity=float(record.get("Quantity", 0.0)),
            UnitPrice=float(record.get("Unit Price", 0.0)),
            PeriodStart=start,
            PeriodEnd=endDate,
        )

    if abs(round(line.Quantity, 5)) < 0.00001:
        line.Quantity = copysign(1, line.Quantity)

    if line.Currency.upper() != "DKK":
        print(line.Currency)
    try:
        line.UnitPrice = round(float(abs(line.Amount)) / float(abs(line.Quantity)), 5)
    except Exception as e:
        print(catName)
    #line.Amount = round(line.Amount, 2)



    return line

