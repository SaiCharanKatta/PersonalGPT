from pathlib import Path
import os, sqlite3
ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("PERSONAL_GPT_DATA_DIR", str(ROOT / "runtime_data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_FILE = DATA_DIR / "personal_gpt.db"
if not DB_FILE.exists():
    with sqlite3.connect(DB_FILE) as conn:
        conn.executescript((ROOT / "schema.sql").read_text())
