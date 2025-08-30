import sys
import tempfile
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import config
import db
from services import settings


def test_configuration_flag() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        config.DB_PATH = f"{tmp}/test.db"
        db.init_db()
        assert settings.is_configured() is False
        settings.set_configured()
        assert settings.is_configured() is True
