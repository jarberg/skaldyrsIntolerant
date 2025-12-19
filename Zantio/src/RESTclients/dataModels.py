from dataclasses import dataclass, field
from datetime import date
from math import copysign
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
    startDate:date
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
class CustomerInvoiceCategoryLineBase:
    ProductFamily: str
    ItemName: str
    ItemNo: int
    CustomerName: str
    Amount: float
    Units: str
    Currency: str
    Quantity: float
    UnitPrice: float
    PeriodStart: date
    PeriodEnd: date

    def __add__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented

        self.Quantity += other.Quantity
        self.Amount += round(other.UnitPrice*other.Quantity, 2)
        self.UnitPrice = round(self.Amount / self.Quantity, 5)

        return self

    def __str__(self) -> str:
        return f"{self.CustomerName} - {self.ItemName} ({self.Quantity})"

    @staticmethod
    def _norm_name(s: str) -> str:
        return " ".join((s or "").split()).casefold()

    def can_merge(self, other) -> bool:
        if not isinstance(other, type(self)):
            return False
        val = self._norm_name(self.ItemName) == self._norm_name(other.ItemName) and self.UnitPrice == other.UnitPrice
        if val:
            pass
            #print(self._norm_name(self.ItemName), " ", self._norm_name(other.ItemName))
        return val

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





