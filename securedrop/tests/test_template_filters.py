from datetime import datetime, timedelta
from pathlib import Path

import i18n
import i18n_tool
import journalist_app
import source_app
import template_filters
from db import db
from flask import session
from sh import pybabel
from tests.test_i18n import create_config_for_i18n_test


def verify_rel_datetime_format(app):
    with app.test_client() as c:
        c.get("/")
        assert session.get("locale") == "en_US"
        result = template_filters.rel_datetime_format(datetime(2016, 1, 1, 1, 1, 1))
        assert "January 1, 2016 at 1:01:01 AM UTC" == result

        result = template_filters.rel_datetime_format(datetime(2016, 1, 1, 1, 1, 1), fmt="yyyy")
        assert "2016" == result

        test_time = datetime.utcnow() - timedelta(hours=2)
        result = template_filters.rel_datetime_format(test_time, relative=True)
        assert "2 hours ago" == result

        c.get("/?l=fr_FR")
        assert session.get("locale") == "fr_FR"
        result = template_filters.rel_datetime_format(datetime(2016, 1, 1, 1, 1, 1))
        assert "1 janvier 2016 à 01:01:01 TU" == result

        result = template_filters.rel_datetime_format(datetime(2016, 1, 1, 1, 1, 1), fmt="yyyy")
        assert "2016" == result

        test_time = datetime.utcnow() - timedelta(hours=2)
        result = template_filters.rel_datetime_format(test_time, relative=True)
        assert "2\xa0heures" in result


def verify_filesizeformat(app):
    with app.test_client() as c:
        c.get("/")
        assert session.get("locale") == "en_US"
        assert "1 byte" == template_filters.filesizeformat(1)
        assert "2 bytes" == template_filters.filesizeformat(2)
        value = 1024 * 3
        assert "3 kB" == template_filters.filesizeformat(value)
        value *= 1024
        assert "3 MB" == template_filters.filesizeformat(value)
        value *= 1024
        assert "3 GB" == template_filters.filesizeformat(value)
        value *= 1024
        assert "3 TB" == template_filters.filesizeformat(value)
        value *= 1024
        assert "3,072 TB" == template_filters.filesizeformat(value)

        c.get("/?l=fr_FR")
        assert session.get("locale") == "fr_FR"
        assert "1\xa0octet" == template_filters.filesizeformat(1)
        assert "2\xa0octets" == template_filters.filesizeformat(2)
        value = 1024 * 3
        assert "3\u202fko" == template_filters.filesizeformat(value)
        value *= 1024
        assert "3\u202fMo" == template_filters.filesizeformat(value)
        value *= 1024
        assert "3\u202fGo" == template_filters.filesizeformat(value)
        value *= 1024
        assert "3\u202fTo" == template_filters.filesizeformat(value)
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

    for l in ("en_US", "fr_FR"):
        pot = test_config.TEMP_DIR / "messages.pot"
        pybabel("init", "-i", pot, "-d", test_config.TEMP_DIR, "-l", l)

    app = create_app(test_config)
    with app.app_context():
        db.create_all()

    assert list(i18n.LOCALES.keys()) == test_config.SUPPORTED_LOCALES
    verify_filesizeformat(app)
    verify_rel_datetime_format(app)
