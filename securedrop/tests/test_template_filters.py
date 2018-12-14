# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import os

from flask import session

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
import i18n
import i18n_tool
import journalist_app
import source_app
import template_filters

from sh import pybabel


def verify_rel_datetime_format(app):
    with app.test_client() as c:
        c.get('/')
        assert session.get('locale') is None
        result = template_filters.rel_datetime_format(
            datetime(2016, 1, 1, 1, 1, 1))
        assert "Jan 01, 2016 01:01 AM" == result

        result = template_filters.rel_datetime_format(
            datetime(2016, 1, 1, 1, 1, 1), fmt="yyyy")
        assert "2016" == result

        test_time = datetime.utcnow() - timedelta(hours=2)
        result = template_filters.rel_datetime_format(test_time,
                                                      relative=True)
        assert "2 hours ago" == result

        c.get('/?l=fr_FR')
        assert session.get('locale') == 'fr_FR'
        result = template_filters.rel_datetime_format(
            datetime(2016, 1, 1, 1, 1, 1))
        assert "janv. 01, 2016 01:01 AM" == result

        result = template_filters.rel_datetime_format(
            datetime(2016, 1, 1, 1, 1, 1), fmt="yyyy")
        assert "2016" == result

        test_time = datetime.utcnow() - timedelta(hours=2)
        result = template_filters.rel_datetime_format(test_time,
                                                      relative=True)
        assert "2 heures" in result


def verify_filesizeformat(app):
    with app.test_client() as c:
        c.get('/')
        assert session.get('locale') is None
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

        c.get('/?l=fr_FR')
        assert session.get('locale') == 'fr_FR'
        assert "1 octet" == template_filters.filesizeformat(1)
        assert "2 octets" == template_filters.filesizeformat(2)
        value = 1024 * 3
        assert "3 ko" == template_filters.filesizeformat(value)
        value *= 1024
        assert "3 Mo" == template_filters.filesizeformat(value)
        value *= 1024
        assert "3 Go" == template_filters.filesizeformat(value)
        value *= 1024
        assert "3 To" == template_filters.filesizeformat(value)
        value *= 1024
        assert "072 To" in template_filters.filesizeformat(value)


# We can't use fixtures because these options are set at app init time, and we
# can't modify them after.
def test_source_filters(source_config):
    do_test(source_config, source_app.create_app)


# We can't use fixtures because these options are set at app init time, and we
# can't modify them after.
def test_journalist_filters(journalist_config):
    do_test(journalist_config, journalist_app.create_app)


def do_test(config, create_app):
    config.SUPPORTED_LOCALES = ['en_US', 'fr_FR']
    config.TRANSLATION_DIRS = config.TEMP_DIR
    i18n_tool.I18NTool().main([
        '--verbose',
        'translate-messages',
        '--mapping', 'tests/i18n/babel.cfg',
        '--translations-dir', config.TEMP_DIR,
        '--sources', 'tests/i18n/code.py',
        '--extract-update',
        '--compile',
    ])

    for l in ('en_US', 'fr_FR'):
        pot = os.path.join(config.TEMP_DIR, 'messages.pot')
        pybabel('init', '-i', pot, '-d', config.TEMP_DIR, '-l', l)

    app = create_app(config)

    assert i18n.LOCALES == config.SUPPORTED_LOCALES
    verify_filesizeformat(app)
    verify_rel_datetime_format(app)
