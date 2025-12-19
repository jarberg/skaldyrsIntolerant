# launch_app.py – bruges til at bygge .exe og starte Streamlit

import os
import sys
import traceback
from pathlib import Path
import webbrowser

# Slå Streamlit dev-mode fra
os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"

# Ensure PyInstaller sees these imports
import streamlit  # noqa: F401
import streamlit.web.cli as stcli  # noqa: F401

# Your app dependencies (optional, but fine to keep)
import pandas  # noqa: F401
import numpy  # noqa: F401
import requests  # noqa: F401
import openpyxl  # noqa: F401
import dotenv  # noqa: F401
import altair  # noqa: F401
import duckdb  # noqa: F401


def get_streamlit_script_path() -> Path:
    """
    Return the path to src/streamlit_app.py both in development
    and when frozen with PyInstaller onefile.

    In onefile mode, PyInstaller extracts data files to sys._MEIPASS.
    """
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS"))  # extraction dir
    else:
        base = Path(__file__).resolve().parent

    return (base / "src" / "streamlit_app.py").resolve()


def main():
    port = 8501
    script_path = get_streamlit_script_path()

    print(f"Starter Streamlit fra: {script_path}")
    print(f"Forventet URL: http://localhost:{port}\n")

    if not script_path.exists():
        print("Kunne ikke finde Streamlit-scriptet i pakken.")
        print("Sørg for at du har bundlet 'src' som --add-data (se kommandoen nedenfor).")
        input("Tryk Enter for at lukke...")
        return

    try:
        # Build argv exactly like "streamlit run <script>"
        sys.argv = [
            "streamlit",
            "run",
            str(script_path),
            "--server.port",
            str(port),
            "--server.headless",
            "true",
            "--browser.gatherUsageStats",
            "false",
        ]

        # Open browser explicitly (Streamlit sometimes won’t in packaged apps)
        webbrowser.open(f"http://localhost:{port}")

        stcli.main()

    except SystemExit:
        # Streamlit CLI can raise SystemExit; treat as normal shutdown
        pass
    except Exception:
        print("\n================= FEJL I STREAMLIT-APPEN =================")
        traceback.print_exc()
        print("==========================================================\n")
        input("Der opstod en fejl. Tryk Enter for at lukke...")
        return

    print("Streamlit er stoppet.")
    input("Tryk Enter for at lukke...")


if __name__ == "__main__":
    main()
