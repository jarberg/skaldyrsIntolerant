from RESTclients.dataModels import CustomerInvoiceCategoryLine_base


def generate_correct_product_line(catName, record):
    if catName == "Exclaimer":
        line = CustomerInvoiceCategoryLine_base(
            Amount=record.get("Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Item Name", "Failed"),
            ItemNo=record.get("Item No", "Failed"),
            Units="stk",
            CustomerName = record.get("Portal Customer Name"),
            ProductFamily=record.get("Subscription Name", "Failed"),
            Quantity=float(record.get("Quantity", 0.0)),
            UnitPrice=record.get("Unit Price", "Failed"),
        )
    elif catName == "SPLA":
        line = CustomerInvoiceCategoryLine_base(
            Amount=record.get("Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Item Name", "Failed"),
            ItemNo=record.get("Item No", "Failed"),
            Units="stk",
            CustomerName=record.get("Portal Customer Name"),
            ProductFamily=record.get("Product Family", "Failed"),
            Quantity=float(record.get("Quantity", 0.0)),
            UnitPrice=record.get("Unit Price", "Failed"),
        )
    elif catName == "Microsoft CSP (NCE)":
        line = CustomerInvoiceCategoryLine_base(
            Amount=record.get("Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Nickname", "Failed"),
            ItemNo=record.get("Item No", "Failed"),
            Units="stk",
            CustomerName=record.get("Portal Customer Name"),
            ProductFamily=record.get("Description", "Failed"),
            Quantity=float(record.get("Quantity", 0.0)),
            UnitPrice=record.get("Unit Price", "Failed"),
        )
    elif catName == "Keepit":
        line = CustomerInvoiceCategoryLine_base(
            Amount=record.get("Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Item Name", "Failed"),
            ItemNo=record.get("Item No", "Failed"),
            Units="stk",
            CustomerName=record.get("Portal Customer Name"),
            ProductFamily=record.get("Connector", "Failed"),
            Quantity=float(record.get("Quantity", 0.0)),
            UnitPrice=record.get("Unit Price", "Failed"),
        )
    elif catName == "Acronis":
        line = CustomerInvoiceCategoryLine_base(
            Amount=record.get("Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Item Name", "Failed"),
            ItemNo=record.get("Item No", "Failed"),
            Units=record.get("Unit", "Failed"),
            CustomerName=record.get("Portal Customer Name"),
            ProductFamily=record.get("Description", "Failed"),
            Quantity=float(record.get("Quantity", 0.0)),
            UnitPrice=record.get("Unit Price", "Failed"),
        )
    elif catName == "Dropbox":
        line = CustomerInvoiceCategoryLine_base(
            Amount=record.get("Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Description", "Failed"),
            ItemNo=record.get("Item No", "Failed"),
            Units="stk",
            CustomerName=record.get("Portal Customer Name"),
            ProductFamily="Dropbox",
            Quantity=float(record.get("License Quantity", 0.0)),
            UnitPrice=record.get("Unit Price", "Failed"),
        )
    elif catName == "Impossible Cloud":
        line = CustomerInvoiceCategoryLine_base(
            Amount=float(record.get("Quantity", 0.0))*50,
            Currency=record.get("Currency", "Failed"),
            ItemName="cloud service",
            ItemNo=record.get("Item No", "Failed"),
            Units="stk",
            CustomerName=record.get("Portal Customer Name"),
            ProductFamily="cloud service",
            Quantity=float(record.get("Quantity", 0.0)),
            UnitPrice=50,
        )
    elif catName == "Microsoft NCE (Azure)":
        line = CustomerInvoiceCategoryLine_base(
            Amount=record.get("Amount", "Failed"),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Description", "Failed"),
            ItemNo=record.get("Product Id", "Failed"),
            Units="stk",
            CustomerName=record.get("Portal Customer Name"),
            ProductFamily=record.get("Product Group"),
            Quantity=float(record.get("License Quantity", 0.0)),
            UnitPrice=record.get("Unit Price", "Failed"),
        )
    else:
        line = CustomerInvoiceCategoryLine_base(
            Amount=float(record.get("Amount", 0.0)),
            Currency=record.get("Currency", "Failed"),
            ItemName=record.get("Description", "Failed"),
            ItemNo=record.get("Item No", "Failed"),
            Units="stk",
            CustomerName=record.get("Portal Customer Name"),
            ProductFamily="Dropbox",
            Quantity=float(record.get("Quantity", 0.0)),
            UnitPrice=float(record.get("Unit Price", 0.0)),
        )
        for id in [line.ItemName, line.ItemNo]:
            temp = convertdict[id]
            if temp:
                line.ItemNo = temp
                break


    return line


convertdict = {
    "Microsoft 365 Business Basic": "91003",
    "Exchange Online (Plan 1)": "CFQ7TTC0LH16",
    "Microsoft 365 Apps for Business" :"91008",
    "Microsoft 365 Business Standard": "98001",
    "Microsoft 365 Business Premium": "91002",
}