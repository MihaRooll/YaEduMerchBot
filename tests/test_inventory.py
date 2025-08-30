import sys
import tempfile
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import config
import db
from services import inventory


def test_add_item() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        config.DB_PATH = f"{tmp}/test.db"
        db.init_db()
        inventory.add_item("M", "Red", 5)
        items = inventory.list_items()
        assert len(items) == 1
        assert items[0]["size"] == "M"
        assert items[0]["color"] == "Red"
        assert items[0]["qty_total"] == 5
