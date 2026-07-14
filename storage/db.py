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
from datetime import datetime, timezone
from pathlib import Path

import bcrypt

logger = logging.getLogger(__name__)

# Default path used by the application.  Tests may override this.
DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "wattif.db"

# ---------------------------------------------------------------------------
# DDL statements
# ---------------------------------------------------------------------------

_DDL_MONTHLY_BILL_RECORDS = """
CREATE TABLE IF NOT EXISTS monthly_bill_records (
    year_month          TEXT NOT NULL,
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
    created_at          TEXT NOT NULL,
    user_id             INTEGER REFERENCES users(id),
    PRIMARY KEY (user_id, year_month)
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

_DDL_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT NOT NULL UNIQUE CHECK(length(email) <= 254),
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL
);
"""

_DDL_SAVED_FORECASTS = """
CREATE TABLE IF NOT EXISTS saved_forecasts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    horizon    INTEGER NOT NULL,
    months     TEXT NOT NULL,
    saved_at   TEXT NOT NULL,
    UNIQUE(user_id)
);
"""

_DDL_USER_SETTINGS = """
CREATE TABLE IF NOT EXISTS user_settings (
    user_id                  INTEGER PRIMARY KEY REFERENCES users(id),
    customer_type            TEXT NOT NULL DEFAULT 'Residential',
    default_forecast_horizon INTEGER NOT NULL DEFAULT 3,
    rate_override            REAL,
    chat_max_history         INTEGER NOT NULL DEFAULT 100,
    chat_auto_clear          INTEGER NOT NULL DEFAULT 0,
    notify_kwh_budget        REAL,
    notify_bill_ceiling      REAL,
    notify_high_consumption  REAL,
    auto_retrain_on_upload   INTEGER NOT NULL DEFAULT 0,
    min_datapoints_to_train  INTEGER NOT NULL DEFAULT 12,
    updated_at               TEXT NOT NULL
);
"""

_ALL_DDL = [
    _DDL_MONTHLY_BILL_RECORDS,
    _DDL_DAILY_AGGREGATES,
    _DDL_MONTHLY_AGGREGATES,
    _DDL_TRAINING_LOG,
    _DDL_DATA_ENTRY_LOG,
    _DDL_CHAT_HISTORY,
    _DDL_USERS,
    _DDL_SAVED_FORECASTS,
    _DDL_USER_SETTINGS,
]


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def _table_has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """Check whether *table* already contains a column named *column*."""
    cursor = conn.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def _run_migrations(conn: sqlite3.Connection) -> None:
    """Run idempotent schema migrations for the account system.

    Steps:
      1. Add ``user_id`` column to tables that lack it.
      1b. Migrate monthly_bill_records to composite PK (user_id, year_month).
      2. Seed the default account (wattif@gmail.com / Wattif123!).
      3. Assign orphaned rows (NULL user_id) to the default account.

    Raises
    ------
    Exception
        Re-raised after logging so the application refuses to start.
    """
    try:
        # --- Step 1: ALTER TABLE migrations ----------------------------------
        tables_needing_user_id = [
            "monthly_bill_records",
            "data_entry_log",
            "chat_history",
            "training_log",
        ]
        for table in tables_needing_user_id:
            if not _table_has_column(conn, table, "user_id"):
                logger.info("Adding user_id column to %s", table)
                conn.execute(
                    f"ALTER TABLE {table} ADD COLUMN user_id INTEGER REFERENCES users(id)"
                )
        conn.commit()

        # --- Step 1b: Migrate monthly_bill_records to composite PK -----------
        # Check if the old schema still has year_month as the sole PK.
        # We detect this by checking the table_info: if user_id is NOT part of
        # the PK (pk column == 0 in pragma), we need to rebuild.
        cursor = conn.execute("PRAGMA table_info(monthly_bill_records)")
        columns_info = cursor.fetchall()
        user_id_is_pk = False
        for col in columns_info:
            if col[1] == "user_id" and col[5] > 0:  # col[5] is the pk flag
                user_id_is_pk = True
                break

        if not user_id_is_pk and _table_has_column(conn, "monthly_bill_records", "user_id"):
            logger.info(
                "Migrating monthly_bill_records to composite PK (user_id, year_month)…"
            )
            conn.execute("""
                CREATE TABLE IF NOT EXISTS monthly_bill_records_new (
                    year_month          TEXT NOT NULL,
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
                    created_at          TEXT NOT NULL,
                    user_id             INTEGER REFERENCES users(id),
                    PRIMARY KEY (user_id, year_month)
                )
            """)
            conn.execute("""
                INSERT OR IGNORE INTO monthly_bill_records_new
                SELECT year_month, kwh, price, meralco_rate, avg_temperature,
                       avg_humidity, total_rainfall_mm, holiday_count, weekend_count,
                       hot_days_count, rainy_days_count, is_el_nino, session_id,
                       created_at, user_id
                FROM monthly_bill_records
            """)
            conn.execute("DROP TABLE monthly_bill_records")
            conn.execute(
                "ALTER TABLE monthly_bill_records_new RENAME TO monthly_bill_records"
            )
            conn.commit()
            logger.info("monthly_bill_records migrated to composite PK successfully.")

        logger.info("Schema migration: user_id columns verified/added.")

        # --- Step 2: Default account seeding ---------------------------------
        cursor = conn.execute(
            "SELECT id FROM users WHERE email = ?", ("wattif@gmail.com",)
        )
        row = cursor.fetchone()
        if row is None:
            logger.info("Seeding default account (wattif@gmail.com).")
            password_hash = bcrypt.hashpw(
                "Wattif123!".encode("utf-8"), bcrypt.gensalt(rounds=12)
            ).decode("utf-8")
            created_at = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
                ("wattif@gmail.com", password_hash, created_at),
            )
            conn.commit()
            # Re-fetch the id after insert
            cursor = conn.execute(
                "SELECT id FROM users WHERE email = ?", ("wattif@gmail.com",)
            )
            row = cursor.fetchone()
        default_user_id = row[0]
        logger.info("Default account id: %s", default_user_id)

        # --- Step 3: Orphaned row assignment ---------------------------------
        for table in tables_needing_user_id:
            if _table_has_column(conn, table, "user_id"):
                result = conn.execute(
                    f"UPDATE {table} SET user_id = ? WHERE user_id IS NULL",
                    (default_user_id,),
                )
                if result.rowcount:
                    logger.info(
                        "Assigned %d orphaned rows in %s to default account.",
                        result.rowcount,
                        table,
                    )
        conn.commit()
        logger.info("Migration complete: orphaned rows assigned.")

    except Exception:
        logger.exception("Account system migration failed — application cannot start.")
        raise


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

    # Run account-system migrations (idempotent).
    _run_migrations(conn)


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
