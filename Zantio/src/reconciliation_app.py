import json
from pathlib import Path

import pandas as pd
import streamlit as st

# ----------------------------------------------------------
# Basisopsætning
# ----------------------------------------------------------
st.set_page_config(
    page_title="CloudFactory → Uniconta afstemning",
    layout="wide",
)

st.title("CloudFactory → Uniconta afstemning")

st.markdown(
    """
Denne dashboard viser resultatet af **`src/main.py`**:

- Succesfulde fakturaer (oprettede salgsordrer i Uniconta)  
- CloudFactory-kunder uden match (`failed_customers.csv`)  
- Kunder uden debitor-match i Uniconta (`failed_debtors_uniconta.csv`)  
"""
)

# ----------------------------------------------------------
# Find reconciliation_summary.json genereret af main.py
# ----------------------------------------------------------
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
recon_path = OUTPUT_DIR / "reconciliation_summary.json"

if not recon_path.exists():
    st.error(
        f"Kunne ikke finde afstemningsfilen:\n\n`{recon_path}`\n\n"
        "Kør først `python src/main.py`, så filerne bliver genereret."
    )
    st.stop()

with recon_path.open("r", encoding="utf-8") as f:
    recon = json.load(f)

# Stier i JSON er fulde filstier, som main.py har skrevet
success_csv = Path(recon["success_csv"])
failed_customers_csv = Path(recon["failed_customers_csv"])
failed_debtors_csv = Path(recon["failed_debtors_csv"])

# ----------------------------------------------------------
# Sammenfatning
# ----------------------------------------------------------
st.subheader("Overblik")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "CloudFactory total (Amount, ekskl. moms)",
        f"{recon['total_cloudfactory_amount']:,.2f} DKK",
    )

with col2:
    st.metric(
        "Bogført mod Uniconta-debitorer\n(antal × enhedspris)",
        f"{recon['total_success_amount']:,.2f} DKK",
    )

with col3:
    st.metric(
        "Ingen debitor i Uniconta\n(antal × enhedspris)",
        f"{recon['total_failed_debtors_amount']:,.2f} DKK",
    )

with col4:
    st.metric(
        "Ingen kundematch i CloudFactory\n(antal × enhedspris)",
        f"{recon['total_failed_cloudfactory_customers_amount']:,.2f} DKK",
    )

# Forklaring til præsentation
st.info(
    """
**Vigtig note om beløbene:**

- **CloudFactory total** (første boks) er beregnet direkte ud fra kolonnen **`Amount`** i CloudFactory-fakturaerne (ekskl. moms).  
- **Bogført mod Uniconta-debitorer**, **Ingen debitor i Uniconta** og **Ingen kundematch i CloudFactory** er beregnet som  
  **antal × enhedspris** pr. linje (altså *Quantity × Unit Price*), summeret pr. kunde (ekskl. moms).

Det betyder, at den første boks viser den officielle CloudFactory-fakturatotal,  
mens de tre andre bokse viser, hvordan det samme beløb fordeler sig, når vi genskaber linjerne som salgsordrer i Uniconta.
"""
)

st.divider()

# ----------------------------------------------------------
# Faner til detaljer
# ----------------------------------------------------------
tabs = st.tabs(
    [
        "Succesfulde fakturaer (Uniconta-ordrer)",
        "Fejlede CloudFactory-kunder",
        "Fejlede Uniconta-debitorer",
    ]
)

# 1) Succesfulde fakturaer
with tabs[0]:
    st.subheader("Succesfulde fakturaer (Uniconta-ordrer)")
    if success_csv.exists():
        df_success = pd.read_csv(success_csv)
        st.write(f"Antal kunder / ordrer: **{len(df_success)}**")
        st.dataframe(df_success, use_container_width=True)
    else:
        st.warning(f"`success_invoices.csv` blev ikke fundet på:\n`{success_csv}`")

# 2) Fejlede CloudFactory-kunder (ingen CF → kundematch)
with tabs[1]:
    st.subheader("Fejlede CloudFactory-kunder (ingen kundematch)")
    if failed_customers_csv.exists():
        df_failed_cf = pd.read_csv(failed_customers_csv)
        st.write(f"Antal rækker: **{len(df_failed_cf)}**")
        st.dataframe(df_failed_cf, use_container_width=True)
    else:
        st.info(
            f"`failed_customers.csv` blev ikke fundet på:\n`{failed_customers_csv}`\n\n"
            "Det kan betyde, at alle CloudFactory-kunder blev matchet korrekt."
        )

# 3) Fejlede Uniconta-debitorer (ingen debitor-match)
with tabs[2]:
    st.subheader("Fejlede Uniconta-debitorer (ingen debitor-match)")
    if failed_debtors_csv.exists():
        df_failed_debtors = pd.read_csv(failed_debtors_csv)
        st.write(f"Antal rækker: **{len(df_failed_debtors)}**")
        st.dataframe(df_failed_debtors, use_container_width=True)
    else:
        st.info(
            f"`failed_debtors_uniconta.csv` blev ikke fundet på:\n`{failed_debtors_csv}`\n\n"
            "Det kan betyde, at alle kunder fik match til en debitor i Uniconta."
        )
