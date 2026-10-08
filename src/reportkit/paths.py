"""Project paths, resolved from this file so commands work from any folder."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "sql"
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
