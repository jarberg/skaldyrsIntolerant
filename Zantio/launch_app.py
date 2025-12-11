# launch_app.py – bruges til at bygge .exe og starte Streamlit

import os

# 🔹 Slå Streamlit dev-mode fra, så den ikke bruger Node-dev-server på port 3000
os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"

import sys
from pathlib import Path
import subprocess
import traceback

# Sørg for at PyInstaller pakker disse moduler med
import streamlit  # noqa: F401
import streamlit.web.cli as stcli  # noqa: F401

# Pakker som din app (streamlit_app.py + main.py) bruger
import pandas  # noqa: F401
import numpy  # noqa: F401
import requests  # noqa: F401
import openpyxl  # noqa: F401
import dotenv  # noqa: F401  # python-dotenv
import altair  # noqa: F401
import duckdb  # noqa: F401


def get_base_dir() -> Path:
    """Find base-mappen, både som .py og som PyInstaller .exe."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    else:
        return Path(__file__).resolve().parent


def main():
    base_dir = get_base_dir()
    src_dir = base_dir / "src"
    script_path = src_dir / "streamlit_app.py"

    if not script_path.exists():
        print(f"Kunne ikke finde Streamlit-scriptet: {script_path}")
        print("Sørg for at mappen 'src' ligger ved siden af .exe-filen.")
        input("Tryk Enter for at lukke...")
        return

    # Klassisk Streamlit-port når dev-mode er slået fra
    port = 8501

    print(f"Starter Streamlit fra: {script_path}")
    print(f"Forventet URL: http://localhost:{port}\n")

    try:
        if getattr(sys, "frozen", False):
            # Kører som .exe → brug Streamlit CLI direkte
            sys.argv = ["streamlit", "run", str(script_path)]
            stcli.main()
        else:
            # Normal Python (til udvikling)
            cmd = [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(script_path),
            ]
            subprocess.run(cmd, cwd=str(src_dir))

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
