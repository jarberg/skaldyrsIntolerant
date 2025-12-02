from dataclasses import dataclass, field
from datetime import date
from typing import  List, Optional, Dict, Any

@dataclass
class PartnerInvoice:
    invoice_number: Optional[str]
    invoice_date: Optional[date]
    lines: Optional[dict]
    extras: Optional[Dict[str, Any]] = field(default_factory=dict)

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
        return self.countryCode+self.vatID

@dataclass
class CustomerInvoiceCategory:
    description: str
    total: float


@dataclass
class CustomerInvoice:
    customer: Customer
    period_start: date
    period_end: date
    categories: List[CustomerInvoiceCategory]



