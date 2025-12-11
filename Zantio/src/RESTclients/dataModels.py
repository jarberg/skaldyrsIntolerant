from dataclasses import dataclass, field
from datetime import date
from typing import  Optional, Dict, Any

@dataclass
class PartnerInvoice:
    invoice_number: Optional[str]
    invoice_date: Optional[date]
    lines: Optional[dict]
    extras: Optional[Dict[str, Any]] = field(default_factory=dict)
    def __iter__(self):
        for key, value in self.extras.items():
            for key2, value2 in value:
                if key not in []:
                    yield key, value

@dataclass
class CloudFactoryInvoiceCategory:
    name: str
    excelLink: str
    extras: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CloudFactoryInvoice:
    endDate:date
    categories: Dict[str, CloudFactoryInvoiceCategory] = field(default_factory=dict)
    extras: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Customer:
    id: Optional[str]
    name: Optional[str]
    vatID: Optional[str]
    countryCode: Optional[str]
    external_id: Optional[str]  # e.g. your ERP customer number
    extras: Optional[Dict[str, Any]] = field(default_factory=dict)

    @property
    def moms_nummer(self) -> str:
        if not self.vatID.isdigit():
            return self.vatID
        return self.countryCode+self.vatID


@dataclass
class CustomerInvoiceCategoryLine_base:
    ProductFamily: str
    ItemName: str
    ItemNo: int
    CustomerName: str
    Amount: float
    Units: str
    Currency: str
    ItemName: str
    Quantity: float
    UnitPrice: float

    def __str__(self) -> str:
        return f"{self.CustomerName} - {self.ItemName} ({self.Quantity})"

@dataclass
class CustomerInvoiceCategory:
    name: str
    lines: list

@dataclass
class CustomerInvoice:
    customer: Customer
    period_start: date
    period_end: date
    categories: Optional[Dict[str, Any]] = field(default_factory=dict)


@dataclass
class CustomerInvoice_Error:
    customer: Customer
    reason: str
    categories: Optional[Dict[str, Any]] = field(default_factory=dict)





