from db import get_connection


def is_configured() -> bool:
    with get_connection() as conn:
        cur = conn.execute("SELECT value FROM settings WHERE key = 'configured'")
        row = cur.fetchone()
        return row is not None and row[0] == '1'


def set_configured() -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings(key, value) VALUES('configured', '1')"
        )
        conn.commit()
