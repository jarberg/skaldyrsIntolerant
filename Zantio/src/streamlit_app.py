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


# ----------------------------
# Streamlit setup
# ----------------------------
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

# ----------------------------
# Session state (admin delete tool)
# ----------------------------
if "erase_orders" not in st.session_state:
    st.session_state.erase_orders = []
if "erase_your_ref" not in st.session_state:
    st.session_state.erase_your_ref = "API-ORDER-001"
if "erase_found_for_ref" not in st.session_state:
    st.session_state.erase_found_for_ref = None
if "erase_last_action" not in st.session_state:
    st.session_state.erase_last_action = None  # "found" / "deleted"

# Step 1 (state til linjer)
if "erase_lines" not in st.session_state:
    st.session_state.erase_lines = []
if "erase_reference_number" not in st.session_state:
    st.session_state.erase_reference_number = "API_TEST"
if "erase_found_for_reference" not in st.session_state:
    st.session_state.erase_found_for_reference = None

# ----------------------------
# Top actions: Afstemning + Slet (samme linje)
# ----------------------------
col_run, col_admin = st.columns([3, 1])

with col_run:
    if st.button("Kør afstemning nu", key="btn_run_reconciliation"):
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

with col_admin:
    # Hele slette-flowet ligger her (ikke i bunden)
    with st.popover("⚠️ Slet Ordrer", use_container_width=True):
        st.markdown("**⚠️ ADVARSEL:** Dette værktøj kan slette data i Uniconta og kan ikke fortrydes.")
        st.caption("Flow: Find (dry-run) → se preview → marker checkbox → SLET NU")

        # Lazy imports + import via filsti (robust i Streamlit)
        admin_import_error = None
        try:
            from dotenv import load_dotenv
            from RESTclients.Uniconta.uniconta import UnicontaClient
            import importlib.util

            erase_path = APP_DIR / "RESTclients" / "erase_sales.py"
            if not erase_path.exists():
                raise FileNotFoundError(f"Kunne ikke finde {erase_path}")

            spec = importlib.util.spec_from_file_location("erase_sales", erase_path)
            erase_sales = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(erase_sales)

            # Step 2 (importér begge sæt funktioner)
            fetch_debtor_orders = erase_sales.fetch_debtor_orders
            delete_debtor_orders = erase_sales.delete_debtor_orders
            fetch_debtor_order_lines = erase_sales.fetch_debtor_order_lines
            delete_debtor_order_lines = erase_sales.delete_debtor_order_lines

        except Exception as e:
            admin_import_error = e

        if admin_import_error is not None:
            st.error(
                "Kunne ikke indlæse admin-sletteværktøjet.\n\n"
                f"Fejl: {admin_import_error}"
            )
        else:
            # Step 3 (mode-selector)
            mode = st.radio(
                "Hvad vil du slette?",
                ["Ordrer (YourRef)", "Linjer (ReferenceNumber)"],
                horizontal=True,
                key="erase_mode_radio",
            )

            # Step 4 (inputs afhænger af mode)
            if mode == "Ordrer (YourRef)":
                your_ref = st.text_input(
                    "YourRef (kun ordrer med denne værdi bliver ramt)",
                    value=st.session_state.erase_your_ref,
                    help="Eksempel: API-ORDER-001",
                    key="erase_yourref_input",
                ).strip()
                st.session_state.erase_your_ref = your_ref or "API-ORDER-001"
            else:
                reference_number = st.text_input(
                    "ReferenceNumber (kun linjer med denne værdi bliver ramt)",
                    value=st.session_state.erase_reference_number,
                    help="Eksempel: API_TEST",
                    key="erase_reference_input",
                ).strip()
                st.session_state.erase_reference_number = reference_number or "API_TEST"

            # Actions in same block
            c1, c2 = st.columns(2)

            with c1:
                find_label = "Find ordrer (dry-run)" if mode == "Ordrer (YourRef)" else "Find linjer (dry-run)"
                if st.button(find_label, type="secondary", key="btn_erase_find"):
                    try:
                        load_dotenv()
                        adapter = UnicontaClient()

                        # Step 5 (branch på mode)
                        if mode == "Ordrer (YourRef)":
                            orders = fetch_debtor_orders(adapter, your_ref=st.session_state.erase_your_ref)
                            st.session_state.erase_orders = orders or []
                            st.session_state.erase_found_for_ref = st.session_state.erase_your_ref
                        else:
                            lines = fetch_debtor_order_lines(
                                adapter,
                                reference_number=st.session_state.erase_reference_number,
                            )
                            st.session_state.erase_lines = lines or []
                            st.session_state.erase_found_for_reference = st.session_state.erase_reference_number

                        st.session_state.erase_last_action = "found"

                    except Exception:
                        st.error("Kunne ikke hente data. Se tekniske detaljer nedenfor.")
                        st.code(traceback.format_exc())

            with c2:
                if st.button("Nulstil", type="secondary", key="btn_erase_reset"):
                    # Step 5 (nulstil begge, så UI ikke er “fordelt”)
                    st.session_state.erase_orders = []
                    st.session_state.erase_found_for_ref = None
                    st.session_state.erase_lines = []
                    st.session_state.erase_found_for_reference = None
                    st.session_state.erase_last_action = None
                    st.rerun()

            # Step 6 (preview + delete afhænger af mode)
            if mode == "Ordrer (YourRef)":
                orders = st.session_state.erase_orders or []
                found_ref = st.session_state.erase_found_for_ref

                if found_ref:
                    st.info(f"Dry-run kørt for YourRef = '{found_ref}'. Fundet **{len(orders)}** ordre(r).")

                if orders:
                    preview_rows = []
                    for o in orders[:50]:
                        preview_rows.append(
                            {
                                "OrderNumber": o.get("OrderNumber"),
                                "Account": o.get("Account"),
                                "Name": o.get("Name"),
                                "YourRef": o.get("YourRef"),
                                "RowId": o.get("RowId"),
                            }
                        )
                    st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, height=220)

                st.markdown("---")
                st.error(
                    "⚠️ SLETNING: Når du trykker **SLET NU**, forsøger app'en at slette ALLE "
                    f"DebtorOrderClient-ordrer med **YourRef = '{st.session_state.erase_your_ref}'**."
                )

                confirm_understand = st.checkbox(
                    "Jeg forstår at dette sletter data i Uniconta og ikke kan fortrydes.",
                    key="erase_confirm_checkbox",
                )

                ready_to_delete = (
                    bool(orders)
                    and (found_ref == st.session_state.erase_your_ref)
                    and confirm_understand
                )

                if not orders:
                    st.warning("Kør først **Find ordrer (dry-run)**, så du kan se hvad der bliver ramt.")

                if st.button("SLET NU", type="primary", disabled=not ready_to_delete, key="btn_erase_delete"):
                    try:
                        load_dotenv()
                        adapter = UnicontaClient()
                        delete_debtor_orders(adapter, orders)

                        st.success(
                            f"✅ Slettede {len(orders)} ordre(r) i Uniconta for YourRef = '{st.session_state.erase_your_ref}'."
                        )

                        st.session_state.erase_orders = []
                        st.session_state.erase_found_for_ref = None
                        st.session_state.erase_last_action = "deleted"

                    except Exception:
                        st.error("❌ Sletning fejlede. Se tekniske detaljer nedenfor.")
                        st.code(traceback.format_exc())

            else:
                lines = st.session_state.erase_lines or []
                found_refnum = st.session_state.erase_found_for_reference

                if found_refnum:
                    st.info(
                        f"Dry-run kørt for ReferenceNumber = '{found_refnum}'. Fundet **{len(lines)}** linje(r)."
                    )

                if lines:
                    preview_rows = []
                    for l in lines[:50]:
                        preview_rows.append(
                            {
                                "OrderNumber": l.get("OrderNumber"),
                                "Item": l.get("Item"),
                                "Text": l.get("Text"),
                                "Qty": l.get("Qty"),
                                "Price": l.get("Price"),
                                "Total": l.get("Total"),
                                "ReferenceNumber": l.get("ReferenceNumber"),
                                "RowId": l.get("RowId"),
                            }
                        )
                    st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, height=220)

                st.markdown("---")
                st.error(
                    "⚠️ SLETNING: Når du trykker **SLET NU**, forsøger app'en at slette ALLE "
                    f"DebtorOrderLineClientUser-linjer med **ReferenceNumber = '{st.session_state.erase_reference_number}'**."
                )

                confirm_understand = st.checkbox(
                    "Jeg forstår at dette sletter data i Uniconta og ikke kan fortrydes.",
                    key="erase_confirm_checkbox_lines",
                )

                ready_to_delete = (
                    bool(lines)
                    and (found_refnum == st.session_state.erase_reference_number)
                    and confirm_understand
                )

                if not lines:
                    st.warning("Kør først **Find linjer (dry-run)**, så du kan se hvad der bliver ramt.")

                if st.button("SLET NU", type="primary", disabled=not ready_to_delete, key="btn_erase_delete_lines"):
                    try:
                        load_dotenv()
                        adapter = UnicontaClient()
                        delete_debtor_order_lines(adapter, lines)

                        st.success(
                            f"✅ Slettede {len(lines)} linje(r) i Uniconta for ReferenceNumber = '{st.session_state.erase_reference_number}'."
                        )

                        st.session_state.erase_lines = []
                        st.session_state.erase_found_for_reference = None
                        st.session_state.erase_last_action = "deleted"

                    except Exception:
                        st.error("❌ Sletning fejlede. Se tekniske detaljer nedenfor.")
                        st.code(traceback.format_exc())

st.divider()

# ----------------------------
# Resten af din app (uændret)
# ----------------------------
summary = load_summary()

if summary is None:
    st.info(
        "Ingen resuméfil fundet endnu. "
        "Kør afstemningen først, eller kontrollér at "
        f"'{SUMMARY_PATH.name}' bliver genereret af main.py."
    )
else:
    cf_total = summary.get("total_cloudfactory_amount", 0.0)
    total_success = summary.get("total_success_amount", 0.0)
    total_failed_debtors = summary.get("total_failed_debtors_amount", 0.0)
    total_failed_cf_customers = summary.get("total_failed_cloudfactory_customers_amount", 0.0)
    total_no_customerid = summary.get("total_no_customerid_amount", 0.0)

    invoice_total = cf_total + total_no_customerid
    notes = summary.get("calculation_notes_da", {})

    st.subheader("Resumé (eks. moms)")

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
        kpi_card("Bogført mod Uniconta-debitorer", total_success, notes.get("booked_to_debtors", ""))
        kpi_card("Linjer uden Customer Id i billing-Excel", total_no_customerid, notes.get("no_customerid", ""))

    with col2:
        kpi_card("Ingen debitor i Uniconta", total_failed_debtors, notes.get("missing_debtors", ""))

    with col3:
        kpi_card("Ingen kundematch i CloudFactory", total_failed_cf_customers, notes.get("missing_cf_customers", ""))

    st.caption("Alle summer er baseret på CloudFactory-feltet 'Amount' i billing-filerne.")

st.divider()

st.subheader("Detaljeret afstemning")

if summary is None:
    st.info("Ingen detaljer endnu. Kør afstemningen først, så bliver CSV-filerne genereret.")
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
