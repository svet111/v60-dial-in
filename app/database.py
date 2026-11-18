import sqlite3
from pathlib import Path
from app.models import BrewCreate, BrewRecord

APP_DIR = Path.home() / ".v60-dial-in"
APP_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = APP_DIR / "v60_brews.db"


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS brews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bean_name TEXT NOT NULL,
                roast_level TEXT NOT NULL,
                coffee_g REAL NOT NULL,
                water_g REAL NOT NULL,
                ratio REAL NOT NULL,
                water_temp_c INTEGER NOT NULL,
                pour_count INTEGER NOT NULL,
                swirl INTEGER NOT NULL,
                drawdown_sec INTEGER NOT NULL,
                taste_score INTEGER NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def insert_brew(brew: BrewCreate, db_path: Path = DB_PATH) -> BrewRecord:
    ratio = round(brew.water_g / brew.coffee_g, 2)
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO brews (
                bean_name, roast_level, coffee_g, water_g, ratio,
                water_temp_c, pour_count, swirl, drawdown_sec, taste_score, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                brew.bean_name.strip(),
                brew.roast_level,
                brew.coffee_g,
                brew.water_g,
                ratio,
                brew.water_temp_c,
                brew.pour_count,
                int(brew.swirl),
                brew.drawdown_sec,
                brew.taste_score,
                brew.notes or "",
            ),
        )
        row = conn.execute("SELECT * FROM brews WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return _row_to_record(row)


def list_brews(bean_name: str | None = None, db_path: Path = DB_PATH) -> list[BrewRecord]:
    with get_connection(db_path) as conn:
        if bean_name:
            rows = conn.execute(
                "SELECT * FROM brews WHERE LOWER(bean_name) = LOWER(?) ORDER BY id DESC",
                (bean_name.strip(),),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM brews ORDER BY id DESC").fetchall()
        return [_row_to_record(r) for r in rows]

def list_bean_names(db_path: Path = DB_PATH) -> list[str]:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT DISTINCT bean_name FROM brews ORDER BY bean_name ASC"
        ).fetchall()
        return [r["bean_name"] for r in rows]

def _row_to_record(row: sqlite3.Row) -> BrewRecord:
    return BrewRecord(
        id=row["id"],
        bean_name=row["bean_name"],
        roast_level=row["roast_level"],
        coffee_g=row["coffee_g"],
        water_g=row["water_g"],
        ratio=row["ratio"],
        water_temp_c=row["water_temp_c"],
        pour_count=row["pour_count"],
        swirl=bool(row["swirl"]),
        drawdown_sec=row["drawdown_sec"],
        taste_score=row["taste_score"],
        notes=row["notes"],
        created_at=str(row["created_at"]),
    )