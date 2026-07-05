"""
SQLite database initialisation and schema migration for WATT-IF.

Provides a single entry point, `init_db(conn)`, that creates all required
tables if they do not yet exist.  Callers are responsible for opening and
closing the connection.

Schema:
  - monthly_bill_records  — one row per billing month (primary data store)
  - training_log          — history of model retraining runs
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

# Default path used by the application.  Tests may override this.
DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "wattif.db"

# ---------------------------------------------------------------------------
# DDL statements
# ---------------------------------------------------------------------------

_DDL_MONTHLY_BILL_RECORDS = """
CREATE TABLE IF NOT EXISTS monthly_bill_records (
    year_month          TEXT PRIMARY KEY,
    kwh                 REAL NOT NULL,
    price               REAL NOT NULL,
    meralco_rate        REAL NOT NULL DEFAULT 0.0,
    avg_temperature     REAL NOT NULL DEFAULT 0.0,
    avg_humidity        REAL NOT NULL DEFAULT 0.0,
    total_rainfall_mm   REAL NOT NULL DEFAULT 0.0,
    holiday_count       INTEGER NOT NULL DEFAULT 0,
    weekend_count       INTEGER NOT NULL DEFAULT 0,
    hot_days_count      INTEGER NOT NULL DEFAULT 0,
    rainy_days_count    INTEGER NOT NULL DEFAULT 0,
    is_el_nino          INTEGER NOT NULL DEFAULT 0,
    session_id          TEXT NOT NULL,
    created_at          TEXT NOT NULL
);
"""

_DDL_DAILY_AGGREGATES = """
CREATE TABLE IF NOT EXISTS daily_aggregates (
    date        TEXT PRIMARY KEY,    -- YYYY-MM-DD
    kwh         REAL NOT NULL,
    price       REAL NOT NULL,
    updated_at  TEXT NOT NULL        -- ISO 8601 datetime
);
"""

_DDL_MONTHLY_AGGREGATES = """
CREATE TABLE IF NOT EXISTS monthly_aggregates (
    year_month  TEXT PRIMARY KEY,    -- YYYY-MM
    kwh         REAL NOT NULL,
    price       REAL NOT NULL,
    updated_at  TEXT NOT NULL        -- ISO 8601 datetime
);
"""

_DDL_TRAINING_LOG = """
CREATE TABLE IF NOT EXISTS training_log (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    trained_at            TEXT NOT NULL,
    previous_mape         REAL,
    new_mape              REAL NOT NULL,
    training_window_start TEXT NOT NULL,   -- YYYY-MM
    training_window_end   TEXT NOT NULL    -- YYYY-MM
);
"""

_DDL_DATA_ENTRY_LOG = """
CREATE TABLE IF NOT EXISTS data_entry_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    year_month   TEXT NOT NULL,
    kwh          REAL NOT NULL,
    bill_amount  REAL,
    label        TEXT,
    source       TEXT NOT NULL CHECK(source IN ('Manual', 'CSV Upload')),
    created_at   TEXT NOT NULL
);
"""

_DDL_CHAT_HISTORY = """
CREATE TABLE IF NOT EXISTS chat_history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    role       TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    text       TEXT NOT NULL CHECK(length(text) >= 1 AND length(text) <= 10000),
    created_at TEXT NOT NULL
);
"""

_ALL_DDL = [
    _DDL_MONTHLY_BILL_RECORDS,
    _DDL_DAILY_AGGREGATES,
    _DDL_MONTHLY_AGGREGATES,
    _DDL_TRAINING_LOG,
    _DDL_DATA_ENTRY_LOG,
    _DDL_CHAT_HISTORY,
]


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def init_db(conn: sqlite3.Connection) -> None:
    """Create all WATT-IF tables in *conn* if they do not already exist.

    Parameters
    ----------
    conn:
        An open :class:`sqlite3.Connection`.  The caller retains ownership
        and must close it when done.
    """
    cursor = conn.cursor()
    for ddl in _ALL_DDL:
        cursor.execute(ddl)
    conn.commit()
    logger.debug("WATT-IF database schema initialised.")


def get_connection(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Return a new SQLite connection to *db_path*, creating it if necessary.

    The parent directory is created automatically.  Row factory is set to
    :class:`sqlite3.Row` so columns can be accessed by name.

    Parameters
    ----------
    db_path:
        Filesystem path to the SQLite database file, or ``":memory:"`` for an
        in-memory database (useful in tests).
    """
    path = Path(db_path)
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrent read performance.
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def create_in_memory_db() -> sqlite3.Connection:
    """Convenience helper: create and initialise a fresh in-memory database.

    Primarily intended for unit tests and the test fixtures in ``conftest.py``.
    """
    conn = get_connection(":memory:")
    init_db(conn)
    return conn
