"""
erase_sales.py

Understøtter to typer oprydning i Uniconta:

1) ORDRE-NIVEAU
   - Finder og sletter DebtorOrderClient
   - Filtreret på YourRef (fx "API-ORDER-001")

2) LINJE-NIVEAU
   - Finder og sletter DebtorOrderLineClientUser
   - Filtreret på ReferenceNumber (fx "API_TEST")

Begge flows understøtter dry-run.
"""

from dotenv import load_dotenv
import sys
from typing import List

from RESTclients.Uniconta.uniconta import UnicontaClient


# ------------------------------------------------------------------
# ORDRE-NIVEAU (DebtorOrderClient)
# ------------------------------------------------------------------

def fetch_debtor_orders(
    adapter: UnicontaClient,
    your_ref: str,
) -> List[dict]:
    """
    Henter alle DebtorOrderClient og filtrerer på YourRef.
    """
    url = f"{adapter.base_url}/Query/Get/DebtorOrderClient"

    payload = [
        {
            "PropertyName": "Account",
            "FilterValue": "",
            "Skip": 0,
            "Take": 0,
            "OrderBy": "true",
            "OrderByDescending": "false",
        }
    ]

    resp = adapter.session.post(url, json=payload)
    if not resp.ok:
        raise RuntimeError(
            f"Query/Get/DebtorOrderClient failed: {resp.status_code} {resp.text}"
        )

    data = resp.json() or []
    filtered = [row for row in data if row.get("YourRef") == your_ref]

    print(f"🔍 DebtorOrderClient total: {len(data)}")
    print(f"🔎 Matcher YourRef='{your_ref}': {len(filtered)}")

    return filtered


def delete_debtor_orders(
    adapter: UnicontaClient,
    orders: List[dict],
):
    """
    Sletter DebtorOrderClient-ordrer.
    """
    if not orders:
        print("✅ Ingen ordrer at slette.")
        return

    url = f"{adapter.base_url}/Crud/DeleteList/DebtorOrderClient"
    resp = adapter.session.delete(url, json=orders)

    if not resp.ok:
        raise RuntimeError(
            f"DeleteList/DebtorOrderClient failed: {resp.status_code} {resp.text}"
        )

    print(f"🗑️  Slettede {len(orders)} DebtorOrderClient-ordrer.")


# ------------------------------------------------------------------
# LINJE-NIVEAU (DebtorOrderLineClientUser)
# ------------------------------------------------------------------

def fetch_debtor_order_lines(
    adapter: UnicontaClient,
    reference_number: str,
) -> List[dict]:
    """
    Henter alle DebtorOrderLineClientUser og filtrerer på ReferenceNumber.
    """
    url = f"{adapter.base_url}/Query/Get/DebtorOrderLineClientUser"

    payload = [
        {
            "PropertyName": "OrderNumber",
            "FilterValue": "",
            "Skip": 0,
            "Take": 0,
            "OrderBy": "true",
            "OrderByDescending": "false",
        }
    ]

    resp = adapter.session.post(url, json=payload)
    if not resp.ok:
        raise RuntimeError(
            f"Query/Get/DebtorOrderLineClientUser failed: {resp.status_code} {resp.text}"
        )

    data = resp.json() or []
    filtered = [
        row for row in data
        if row.get("ReferenceNumber") == reference_number
    ]

    print(f"🔍 DebtorOrderLineClientUser total: {len(data)}")
    print(f"🔎 Matcher ReferenceNumber='{reference_number}': {len(filtered)}")

    return filtered


def delete_debtor_order_lines(
    adapter: UnicontaClient,
    lines: List[dict],
):
    """
    Sletter DebtorOrderLineClientUser-linjer.
    """
    if not lines:
        print("✅ Ingen linjer at slette.")
        return

    url = f"{adapter.base_url}/Crud/DeleteList/DebtorOrderLineClientUser"
    resp = adapter.session.delete(url, json=lines)

    if not resp.ok:
        raise RuntimeError(
            f"DeleteList/DebtorOrderLineClientUser failed: {resp.status_code} {resp.text}"
        )

    print(f"🗑️  Slettede {len(lines)} ordrelinjer.")


# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------

def main(
    *,
    mode: str,
    dry_run: bool = True,
    your_ref: str | None = None,
    reference_number: str | None = None,
):
    """
    mode:
      - "orders" → slet DebtorOrderClient via YourRef
      - "lines"  → slet DebtorOrderLineClientUser via ReferenceNumber
    """
    load_dotenv()
    adapter = UnicontaClient()

    if mode == "orders":
        if not your_ref:
            pass
            #raise ValueError("your_ref skal angives i mode='orders'")

        orders = fetch_debtor_orders(adapter, your_ref)

        if not orders:
            print("Ingen matchende ordrer.")
            return

        print("\nEksempel (første 5):")
        for o in orders[:5]:
            print(
                f"OrderNumber={o.get('OrderNumber')} "
                f"Account={o.get('Account')} "
                f"YourRef={o.get('YourRef')}"
            )

        if dry_run:
            print("\n💡 DRY RUN – ingen ordrer slettes.")
            return

        print("\n⚠️ SLETTER ORDRER…")
        delete_debtor_orders(adapter, orders)

    elif mode == "lines":
        if not reference_number:
            raise ValueError("reference_number skal angives i mode='lines'")

        lines = fetch_debtor_order_lines(adapter, reference_number)

        if not lines:
            print("Ingen matchende linjer.")
            return

        print("\nEksempel (første 5):")
        for l in lines[:5]:
            print(
                f"OrderNumber={l.get('OrderNumber')} "
                f"Item={l.get('Item')} "
                f"ReferenceNumber={l.get('ReferenceNumber')}"
            )

        if dry_run:
            print("\n💡 DRY RUN – ingen linjer slettes.")
            return

        print("\n⚠️ SLETTER ORDRELINJER…")
        delete_debtor_order_lines(adapter, lines)

    else:
        raise ValueError("mode skal være 'orders' eller 'lines'")


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------

if __name__ == "__main__":
    """
    Eksempler:

    # Dry-run ordre-sletning
    python erase_sales.py orders API-ORDER-001

    # Live ordre-sletning
    python erase_sales.py orders API-ORDER-001 live

    # Dry-run linje-sletning
    python erase_sales.py lines API_TEST

    # Live linje-sletning
    python erase_sales.py lines API_TEST live
    """
    main(
        mode="orders",
        your_ref="API-ORDER-001",
        dry_run=False,
    )
    if len(sys.argv) < 3:
        print("Usage: erase_sales.py <orders|lines> <value> [live]")
        sys.exit(1)

    mode = sys.argv[1]
    value = sys.argv[2]
    live = len(sys.argv) > 3 and sys.argv[3].lower() == "live"

    if mode == "orders":
        main(
            mode="orders",
            your_ref=value,
            dry_run=not live,
        )
    elif mode == "lines":
        main(
            mode="lines",
            reference_number=value,
            dry_run=not live,
        )
    else:
        main(
            mode="orders",
            your_ref="API-ORDER-001",
            dry_run=not live,
        )
        raise ValueError("mode skal være 'orders' eller 'lines'")
