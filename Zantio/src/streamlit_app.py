# streamlit_app.py
#
# Simpelt interface til Jeppe:
# - Én knap: kør afstemning (main.py)
# - Viser totals fra reconciliation_summary.json
# - Viser tabeller for succes, fejl og linjer uden customer id
#
# Forventet struktur:
#   Zantio/
#     src/
#       main.py
#       streamlit_app.py
#       output/
#         reconciliation_summary.json
#         success_invoices.csv
#         failed_customers.csv
#         failed_debtors_uniconta.csv
#         no_customerid_lines.csv
from dotenv import load_dotenv

load_dotenv()

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# Sti-opsætning
# ---------------------------------------------------------
APP_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = APP_DIR / "output"

SUMMARY_PATH = OUTPUT_DIR / "reconciliation_summary.json"


# ---------------------------------------------------------
# Hjælpefunktioner
# ---------------------------------------------------------
def run_main_script():
    """Kør main.py med samme Python som Streamlit bruger."""
    script_path = APP_DIR / "main.py"

    if not script_path.exists():
        st.error(f"Kunne ikke finde main.py i {APP_DIR}")
        return None

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
    except Exception as e:
        st.error(f"Kunne ikke starte main.py: {e}")
        return None

    return result


def load_summary():
    """Læs JSON-resumé af afstemningen."""
    if not SUMMARY_PATH.exists():
        return None

    try:
        with SUMMARY_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        st.error(f"Kunne ikke læse {SUMMARY_PATH.name}: {e}")
        return None

    return data


def load_csv(path_str: str):
    """Læs en CSV-fil, hvis stien findes. path_str kommer fra JSON'en."""
    if not path_str:
        return None

    path = Path(path_str)
    if not path.is_absolute():
        # Hvis JSON'en indeholder relative stier, antag de er relative til OUTPUT_DIR
        path = OUTPUT_DIR / path_str

    if not path.exists():
        return None

    try:
        df = pd.read_csv(path)
    except Exception:
        try:
            df = pd.read_csv(path, sep=";")
        except Exception as e:
            st.error(f"Kunne ikke læse {path.name}: {e}")
            return None

    return df


def format_currency(value):
    try:
        return f"{float(value):,.2f} DKK".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "-"


# ---------------------------------------------------------
# UI
# ---------------------------------------------------------
st.set_page_config(
    page_title="CloudFactory ↔ Uniconta afstemning",
    layout="wide",
)

st.title("CloudFactory ↔ Uniconta afstemning")

st.markdown(
    """
Denne side er lavet, så afstemningen kan køres **med ét klik** uden at åbne Python-kode.

Tallene herunder er baseret på **CloudFactory-beløbet `Amount`** i billing-Excel.
Alle summer i resuméet er ekskl. moms.
"""
)

st.divider()

# ---------------------------------------------------------
# Kør-knap
# ---------------------------------------------------------
if st.button("Kør afstemning nu"):
    with st.spinner("Afstemning kører..."):
        result = run_main_script()

    if result is None:
        st.stop()

    if result.returncode != 0:
        st.error("Afstemningen gav en fejl. (Se detaljer nedenfor).")
        with st.expander("Tekniske detaljer (valgfrit)"):
            st.subheader("Standard output")
            st.code(result.stdout or "(ingen output)")
            st.subheader("Fejlmeddelelser")
            st.code(result.stderr or "(ingen fejlmeddelelser)")
    else:
        st.success("Afstemningen er gennemført uden fejl.")
        with st.expander("Tekniske detaljer (valgfrit)"):
            st.subheader("Standard output")
            st.code(result.stdout or "(ingen output)")
            if result.stderr:
                st.subheader("Fejlmeddelelser")
                st.code(result.stderr)

st.divider()

# ---------------------------------------------------------
# Resumé-bokse
# ---------------------------------------------------------
summary = load_summary()

if summary is None:
    st.info(
        "Ingen resuméfil fundet endnu. "
        "Kør afstemningen først, eller kontrollér at "
        f"'{SUMMARY_PATH.name}' bliver genereret af main.py."
    )
else:
    # Hent totals fra JSON
    cf_total = summary.get("total_cloudfactory_amount", 0.0)
    total_success = summary.get("total_success_amount", 0.0)
    total_failed_debtors = summary.get("total_failed_debtors_amount", 0.0)
    total_failed_cf_customers = summary.get("total_failed_cloudfactory_customers_amount", 0.0)
    total_no_customerid = summary.get("total_no_customerid_amount", 0.0)

    notes = summary.get("calculation_notes_da", {})

    st.subheader("Resumé (eks. moms)")

    st.info(
        f"**CloudFactory total (per kunde, med kunde-id):** {format_currency(cf_total)}"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Bogført mod Uniconta-debitorer",
            value=format_currency(total_success),
        )
        if "booked_to_debtors" in notes:
            st.caption(notes["booked_to_debtors"])

    with col2:
        st.metric(
            label="Ingen debitor i Uniconta",
            value=format_currency(total_failed_debtors),
        )
        if "missing_debtors" in notes:
            st.caption(notes["missing_debtors"])

    with col3:
        st.metric(
            label="Ingen kundematch i CloudFactory",
            value=format_currency(total_failed_cf_customers),
        )
        if "missing_cf_customers" in notes:
            st.caption(notes["missing_cf_customers"])

    st.metric(
        label="Linjer uden Customer Id i billing-Excel",
        value=format_currency(total_no_customerid),
    )
    if "no_customerid" in notes:
        st.caption(notes["no_customerid"])

    st.caption(
        "Alle summer er baseret på CloudFactory-feltet 'Amount' i billing-filerne."
    )

st.divider()

# ---------------------------------------------------------
# Detaljetabeller
# ---------------------------------------------------------
st.subheader("Detaljeret afstemning")

if summary is None:
    st.info(
        "Ingen detaljer endnu. Kør afstemningen først, så bliver CSV-filerne genereret."
    )
else:
    success_csv = summary.get("success_csv")
    failed_customers_csv = summary.get("failed_customers_csv")
    failed_debtors_csv = summary.get("failed_debtors_csv")
    no_customerid_csv = summary.get("no_customerid_csv")

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Succesfulde kunder (bogført i Uniconta)",
            "Kundefejl i CloudFactory",
            "Ingen debitor i Uniconta",
            "Linjer uden Customer Id",
        ]
    )

    with tab1:
        df_success = load_csv(success_csv)
        if df_success is None:
            st.info("Ingen CSV med succesfulde fakturaer fundet endnu.")
        else:
            st.dataframe(df_success, use_container_width=True, height=400)
            st.download_button(
                "Download succes-CSV",
                data=df_success.to_csv(index=False).encode("utf-8"),
                file_name="success_invoices.csv",
                mime="text/csv",
            )

    with tab2:
        df_failed_cf = load_csv(failed_customers_csv)
        if df_failed_cf is None:
            st.info("Ingen CSV med CloudFactory-kundefejl fundet endnu.")
        else:
            st.dataframe(df_failed_cf, use_container_width=True, height=400)
            st.download_button(
                "Download CloudFactory-kundefejl-CSV",
                data=df_failed_cf.to_csv(index=False).encode("utf-8"),
                file_name="failed_customers.csv",
                mime="text/csv",
            )

    with tab3:
        df_failed_debtors = load_csv(failed_debtors_csv)
        if df_failed_debtors is None:
            st.info("Ingen CSV med Uniconta-debitorfejl fundet endnu.")
        else:
            st.dataframe(df_failed_debtors, use_container_width=True, height=400)
            st.download_button(
                "Download debitorfejl-CSV",
                data=df_failed_debtors.to_csv(index=False).encode("utf-8"),
                file_name="failed_debtors_uniconta.csv",
                mime="text/csv",
            )

    with tab4:
        df_no_id = load_csv(no_customerid_csv)
        if df_no_id is None:
            st.info("Ingen CSV med linjer uden Customer Id fundet endnu.")
        else:
            st.dataframe(df_no_id, use_container_width=True, height=400)
            st.download_button(
                "Download 'no customer id'-CSV",
                data=df_no_id.to_csv(index=False).encode("utf-8"),
                file_name="no_customerid_lines.csv",
                mime="text/csv",
            )
