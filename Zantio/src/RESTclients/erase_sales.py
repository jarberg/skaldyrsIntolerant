"""
delete_uniconta_orders.py

Sletter alle DebtorOrderClient-ordrer, der er oprettet via API'et
med YourRef = "API-ORDER-001", ved hjælp af Uniconta Swagger-endpoints:

  - POST /Query/Get/DebtorOrderClient   (for at hente ordrer)
  - DELETE /Crud/DeleteList/DebtorOrderClient  (for at slette dem)

Forudsætter:
  - uniconta.py med UnicontaAdapter (som du allerede har)
  - ERP_BASE_URL, ERP_API_TOKEN, ERP_USERNAME, ERP_PASSWORD i .env
"""

from dotenv import load_dotenv
import sys
from pathlib import Path

# Tilpas import-stien hvis nødvendigt
# Antager at denne fil ligger i samme "src" som uniconta.py
from RESTclients.uniconta import UnicontaClient


def fetch_debtor_orders(adapter: UnicontaClient, your_ref: str = "API-ORDER-001"):
    """
    Henter alle DebtorOrderClient-ordrer og filtrerer dem i Python på YourRef.
    Vi bruger samme Query/Get-format som til DebtorClient i din eksisterende kode.
    """
    url = f"{adapter.base_url}/Query/Get/DebtorOrderClient"

    payload = [
        {
            "PropertyName": "Account",   # bruges blot som sorteringsfelt; FilterValue "" = hent alle
            "FilterValue": "",
            "Skip": 0,
            "Take": 0,                  # 0 = hent alle rækker
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
    print(f"🔍 Fik {len(data)} DebtorOrderClient-rækker tilbage fra Uniconta.")

    # Filtrér kun de ordrer, vi selv har lavet med YourRef = 'API-ORDER-001'
    filtered = [row for row in data if (row.get("YourRef") == your_ref)]

    print(f"🔎 Heraf matcher {len(filtered)} rækker YourRef = '{your_ref}'.")
    return filtered


def delete_debtor_orders(adapter: UnicontaClient, orders: list[dict]):
    """
    Sletter en liste af DebtorOrderClient-ordrer via:
      DELETE /Crud/DeleteList/DebtorOrderClient

    Vi sender hele order-objekterne, som vi fik dem fra Query/Get.
    Uniconta bruger de nødvendige nøgler (f.eks. RowId) indefra.
    """
    if not orders:
        print("✅ Ingen ordrer at slette – listen er tom.")
        return

    url = f"{adapter.base_url}/Crud/DeleteList/DebtorOrderClient"

    # OBS: DELETE med body – Swagger siger det er sådan.
    resp = adapter.session.delete(url, json=orders)
    if not resp.ok:
        raise RuntimeError(
            f"DeleteList/DebtorOrderClient failed: {resp.status_code} {resp.text}"
        )

    print(f"🗑️  Slettede {len(orders)} DebtorOrderClient-ordrer i Uniconta.")


def main(dry_run: bool = True, your_ref: str = "API-ORDER-001"):
    """
    Hvis dry_run = True:
      - Vi logger ind
      - Finder alle ordrer med YourRef = your_ref
      - Printer dem, men sletter IKKE

    Hvis dry_run = False:
      - Samme som ovenfor, men vi kalder delete_debtor_orders(...)
    """
    load_dotenv()

    print("🔐 Logger ind i Uniconta...")
    adapter = UnicontaClient()

    print(f"🔎 Søger efter DebtorOrderClient-ordrer med YourRef = '{your_ref}'...")
    orders = fetch_debtor_orders(adapter, your_ref=your_ref)

    if not orders:
        print("✅ Ingen ordrer fundet med den YourRef – intet at slette.")
        return

    # Lille oversigt
    print("\nEksempel på de første 5 ordrer:")
    for row in orders[:5]:
        print(
            f"  OrderNumber={row.get('OrderNumber')} "
            f"Account={row.get('Account')} "
            f"Name={row.get('Name')} "
            f"YourRef={row.get('YourRef')}"
        )

    if dry_run:
        print(
            "\n💡 DRY RUN: der bliver IKKE sendt nogen DELETE-kald.\n"
            "Kør scriptet med dry_run=False for rent faktisk at slette."
        )
        return

    # Slet for alvor
    print("\n⚠️ ADVARSEL: Nu slettes alle ovenstående ordrer i Uniconta...")
    delete_debtor_orders(adapter, orders)


if __name__ == "__main__":
    # Eksempel:
    #   python delete_uniconta_orders.py          → kører som dry-run (ingen sletning)
    #   python delete_uniconta_orders.py live     → sletter faktisk
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    dry =False#not (arg.lower() in ["live", "delete", "prod"])
    main(dry_run=dry, your_ref="API-ORDER-001")
