import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).with_name("app.db")


def _get_conn():
    # Use a short-lived connection per call for Streamlit safety.
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they do not exist."""
    with _get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                upload_time TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cleaned_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER NOT NULL,
                csv_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (dataset_id) REFERENCES datasets (id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER NOT NULL,
                report_text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (dataset_id) REFERENCES datasets (id)
            )
            """
        )


def save_dataset(name):
    """Persist dataset metadata and return its ID."""
    with _get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO datasets (name, upload_time) VALUES (?, ?)",
            (name, datetime.utcnow().isoformat()),
        )
        return int(cur.lastrowid)


def save_cleaned_data(dataset_id, df):
    """Persist a single cleaned snapshot per dataset."""
    csv_data = df.to_csv(index=False)
    with _get_conn() as conn:
        conn.execute(
            "DELETE FROM cleaned_data WHERE dataset_id = ?",
            (dataset_id,),
        )
        conn.execute(
            "INSERT INTO cleaned_data (dataset_id, csv_data, created_at) VALUES (?, ?, ?)",
            (dataset_id, csv_data, datetime.utcnow().isoformat()),
        )


def save_report(dataset_id, report_text):
    """Persist a report for a dataset."""
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO reports (dataset_id, report_text, created_at) VALUES (?, ?, ?)",
            (dataset_id, report_text, datetime.utcnow().isoformat()),
        )


def get_datasets():
    """Return list of saved datasets (id, name, upload_time)."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT id, name, upload_time FROM datasets ORDER BY upload_time DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_reports(dataset_id):
    """Return list of reports for a dataset."""
    with _get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, report_text, created_at
            FROM reports
            WHERE dataset_id = ?
            ORDER BY created_at DESC
            """,
            (dataset_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_cleaned_data(dataset_id):
    """Return latest cleaned CSV text for a dataset, or None."""
    with _get_conn() as conn:
        row = conn.execute(
            """
            SELECT csv_data, created_at
            FROM cleaned_data
            WHERE dataset_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (dataset_id,),
        ).fetchone()
    return dict(row) if row else None
