from RESTclients.dataModels import CustomerInvoiceCategoryLineBase


def generate_correct_product_line(catName, record, startDate, endDate):

    if catName == "Exclaimer":
        line = CustomerInvoiceCategoryLineBase(
            Amount=record.get("Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Item Name", "Failed"),
            ItemNo=record.get("Item No", "Failed"),
            Units="stk",
            CustomerName = record.get("Portal Customer Name"),
            ProductFamily=record.get("Subscription Name", "Failed"),
            Quantity=float(record.get("Quantity", 0.0)),
            UnitPrice=record.get("Unit Price", "Failed"),
            PeriodStart=startDate,
            PeriodEnd=endDate,
        )
    elif catName == "SPLA":
        line = CustomerInvoiceCategoryLineBase(
            Amount=record.get("Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Item Name", "Failed"),
            ItemNo=record.get("Item No", "Failed"),
            Units="stk",
            CustomerName=record.get("Portal Customer Name"),
            ProductFamily=record.get("Product Family", "Failed"),
            Quantity=float(record.get("Quantity", 0.0)),
            UnitPrice=record.get("Unit Price", "Failed"),
            PeriodStart=record.get("Start Date", "Failed"),
            PeriodEnd=record.get("End Date", "Failed"),
        )
    elif catName == "Microsoft CSP (NCE)":
        line = CustomerInvoiceCategoryLineBase(
            Amount=record.get("Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Nickname", "Failed"),
            ItemNo=record.get("Item No", "Failed"),
            Units="stk",
            CustomerName=record.get("Portal Customer Name"),
            ProductFamily=record.get("Description", "Failed"),
            Quantity=float(record.get("Quantity", 0.0)),
            UnitPrice=record.get("Unit Price", "Failed"),
            PeriodStart=record.get("Start Date", "Failed"),
            PeriodEnd=record.get("End Date", "Failed"),
        )
    elif catName == "Keepit":
        line = CustomerInvoiceCategoryLineBase(
            Amount=record.get("Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Item Name", "Failed"),
            ItemNo=record.get("Item No", "Failed"),
            Units="stk",
            CustomerName=record.get("Portal Customer Name"),
            ProductFamily=record.get("Connector", "Failed"),
            Quantity=float(record.get("Quantity", 0.0)),
            UnitPrice=record.get("Unit Price", "Failed"),
            PeriodStart=record.get("Start Date", "Failed"),
            PeriodEnd=record.get("End Date", "Failed"),
        )
    elif catName == "Acronis":
        line = CustomerInvoiceCategoryLineBase(
            Amount=record.get("Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Item Name", "Failed"),
            ItemNo=record.get("Item No", "Failed"),
            Units=record.get("Unit", "Failed"),
            CustomerName=record.get("Portal Customer Name"),
            ProductFamily=record.get("Description", "Failed"),
            Quantity=float(record.get("Quantity", 0.0)),
            UnitPrice=record.get("Unit Price", "Failed"),
            PeriodStart=startDate,
            PeriodEnd=endDate
        )
    elif catName == "Dropbox":
        line = CustomerInvoiceCategoryLineBase(
            Amount=record.get("Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Description", "Failed"),
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
            Amount=record.get("Amount", 0.0),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Description", "Failed"),
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
        line = CustomerInvoiceCategoryLineBase(
            Amount=float(record.get("Amount", 0.0)),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Description", "Failed"),
            ItemNo=record.get("Item No", "Failed"),
            Units="stk",
            CustomerName=record.get("Portal Customer Name"),
            ProductFamily="Dropbox",
            Quantity=float(record.get("Quantity", 0.0)),
            UnitPrice=float(record.get("Unit Price", 0.0)),
            PeriodStart=startDate,
            PeriodEnd=endDate,
        )

    return line

