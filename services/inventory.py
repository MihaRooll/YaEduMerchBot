from typing import List, Dict

from db import get_connection


def add_item(size: str, color: str, qty_total: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO inventory(size, color, qty_total) VALUES(?, ?, ?)",
            (size, color, qty_total),
        )
        conn.commit()


def list_items() -> List[Dict[str, str]]:
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT size, color, qty_total, qty_reserved FROM inventory"
        )
        return [dict(row) for row in cur.fetchall()]
