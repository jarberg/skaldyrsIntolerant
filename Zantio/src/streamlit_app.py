
import json
import io
import traceback
import subprocess
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = APP_DIR / "reconcilliation" / "output"
SUMMARY_PATH = OUTPUT_DIR / "reconciliation_summary.json"

def run_main_script():
    """Kør main.py med samme Python som Streamlit bruger."""
    script_path = APP_DIR / "main.py"
    if not script_path.exists():
        st.error(f"Kunne ikke finde main.py i {APP_DIR}")
        return None

    try:
        from dotenv import load_dotenv
        load_dotenv()

        # Capture stdout/stderr
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()

        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            import main
            rc = main.main()

        returncode = 0 if rc in (None, 0) else int(rc)

        return subprocess.CompletedProcess(
            args=["main.main"],
            returncode=returncode,
            stdout=stdout_buf.getvalue(),
            stderr=stderr_buf.getvalue(),
        )

    except Exception:
        # Include any captured output plus traceback
        tb = traceback.format_exc()
        return subprocess.CompletedProcess(
            args=["main.main"],
            returncode=1,
            stdout="",
            stderr=tb,
        )

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

summary = load_summary()

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

    # Samlet fakturasum (inkl. linjer uden Customer Id)
    invoice_total = cf_total + total_no_customerid

    notes = summary.get("calculation_notes_da", {})

    st.subheader("Resumé (eks. moms)")

    # --- PowerBI-style top KPI (fakturatotal) ---
    top_card = f"""
    <div style="
        padding: 18px 22px;
        border-radius: 10px;
        background: #0b1120;
        border: 1px solid #1f2937;
        margin-bottom: 18px;
    ">
      <div style="
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 0.14em;
          color: #9ca3af;
          font-weight: 600;
      ">
        CloudFactory fakturatotal (inkl. linjer uden Customer Id)
      </div>
      <div style="
          font-size: 32px;
          font-weight: 800;
          margin-top: 4px;
          color: #f9fafb;
      ">
        {format_currency(invoice_total)}
      </div>
      <div style="
          font-size: 12px;
          color: #9ca3af;
          margin-top: 4px;
      ">
        Ekskl. moms. Beregnet ud fra CloudFactory-feltet 'Amount' i billing-filerne.
      </div>
    </div>
    """
    st.markdown(top_card, unsafe_allow_html=True)

    # --- Fordeling i 3 kolonner (ens layout) ---
    col1, col2, col3 = st.columns(3)

    def kpi_card(label: str, value: float, note: str | None = None):
        note_html = f"<div style='font-size:11px; color:#9ca3af; margin-top:4px;'>{note}</div>" if note else ""
        html = f"""
        <div style="
            padding: 14px 16px;
            border-radius: 10px;
            background: #020617;
            border: 1px solid #1e293b;
            margin-bottom: 10px;
            height: 100%;
        ">
          <div style="
              font-size:11px;
              text-transform:uppercase;
              letter-spacing:0.12em;
              color:#9ca3af;
              font-weight:600;
          ">
            {label}
          </div>
          <div style="
              font-size:22px;
              font-weight:700;
              margin-top:4px;
              color:#e5e7eb;
          ">
            {format_currency(value)}
          </div>
          {note_html}
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

    with col1:
        kpi_card(
            "Bogført mod Uniconta-debitorer",
            total_success,
            notes.get("booked_to_debtors", "")
        )

        # Linjer uden Customer Id sammen med bogført i venstre kolonne
        kpi_card(
            "Linjer uden Customer Id i billing-Excel",
            total_no_customerid,
            notes.get("no_customerid", "")
        )

    with col2:
        kpi_card(
            "Ingen debitor i Uniconta",
            total_failed_debtors,
            notes.get("missing_debtors", "")
        )

    with col3:
        kpi_card(
            "Ingen kundematch i CloudFactory",
            total_failed_cf_customers,
            notes.get("missing_cf_customers", "")
        )

    st.caption(
        "Alle summer er baseret på CloudFactory-feltet 'Amount' i billing-filerne."
    )

st.divider()

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
