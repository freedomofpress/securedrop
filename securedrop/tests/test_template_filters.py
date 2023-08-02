import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import i18n_tool
import journalist_app
import source_app
import template_filters
from db import db
from flask import session
from tests.test_i18n import create_config_for_i18n_test


def verify_rel_datetime_format(app):
    with app.test_client() as c:
        c.get("/")
        assert session.get("locale") == "en_US"
        result = template_filters.rel_datetime_format(datetime(2016, 1, 1, 1, 1, 1))
        assert result == "January 1, 2016 at 1:01:01 AM UTC"

        result = template_filters.rel_datetime_format(datetime(2016, 1, 1, 1, 1, 1), fmt="yyyy")
        assert result == "2016"

        test_time = datetime.utcnow() - timedelta(hours=2)
        result = template_filters.rel_datetime_format(test_time, relative=True)
        assert result == "2 hours ago"

        c.get("/?l=fr_FR")
        assert session.get("locale") == "fr_FR"
        result = template_filters.rel_datetime_format(datetime(2016, 1, 1, 1, 1, 1))
        assert result == "1 janvier 2016 à 01:01:01 TU"

        result = template_filters.rel_datetime_format(datetime(2016, 1, 1, 1, 1, 1), fmt="yyyy")
        assert result == "2016"

        test_time = datetime.utcnow() - timedelta(hours=2)
        result = template_filters.rel_datetime_format(test_time, relative=True)
        assert "2\xa0heures" in result


def verify_filesizeformat(app):
    with app.test_client() as c:
        c.get("/")
        assert session.get("locale") == "en_US"
        assert template_filters.filesizeformat(1) == "1 byte"
        assert template_filters.filesizeformat(2) == "2 bytes"
        value = 1024 * 3
        assert template_filters.filesizeformat(value) == "3 kB"
        value *= 1024
        assert template_filters.filesizeformat(value) == "3 MB"
        value *= 1024
        assert template_filters.filesizeformat(value) == "3 GB"
        value *= 1024
        assert template_filters.filesizeformat(value) == "3 TB"
        value *= 1024
        assert template_filters.filesizeformat(value) == "3,072 TB"

        c.get("/?l=fr_FR")
        assert session.get("locale") == "fr_FR"
        assert template_filters.filesizeformat(1) == "1\xa0octet"
        assert template_filters.filesizeformat(2) == "2\xa0octets"
        value = 1024 * 3
        assert template_filters.filesizeformat(value) == "3\u202fko"
        value *= 1024
        assert template_filters.filesizeformat(value) == "3\u202fMo"
        value *= 1024
        assert template_filters.filesizeformat(value) == "3\u202fGo"
        value *= 1024
        assert template_filters.filesizeformat(value) == "3\u202fTo"
        value *= 1024
        assert "072\u202fTo" in template_filters.filesizeformat(value)


# We can't use fixtures because these options are set at app init time, and we
# can't modify them after.
def test_source_filters():
    do_test(source_app.create_app)


# We can't use fixtures because these options are set at app init time, and we
# can't modify them after.
def test_journalist_filters():
    do_test(journalist_app.create_app)


def do_test(create_app):
    test_config = create_config_for_i18n_test(supported_locales=["en_US", "fr_FR"])

    i18n_dir = Path(__file__).absolute().parent / "i18n"
    i18n_tool.I18NTool().main(
        [
            "--verbose",
            "translate-messages",
            "--mapping",
            str(i18n_dir / "babel.cfg"),
            "--translations-dir",
            str(test_config.TEMP_DIR),
            "--sources",
            str(i18n_dir / "code.py"),
            "--extract-update",
            "--compile",
        ]
    )

    for lang in ("en_US", "fr_FR"):
        pot = Path(test_config.TEMP_DIR) / "messages.pot"
        subprocess.check_call(
            ["pybabel", "init", "-i", pot, "-d", test_config.TEMP_DIR, "-l", lang]
        )

    app = create_app(test_config)
    with app.app_context():
        db.create_all()

    assert list(app.config["LOCALES"].keys()) == test_config.SUPPORTED_LOCALES
    verify_filesizeformat(app)
    verify_rel_datetime_format(app)
