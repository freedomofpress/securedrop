# -*- coding: utf-8 -*-
import argparse
import logging
from datetime import datetime, timedelta
import os

from flask import session

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
import config
import i18n
import journalist
import manage
import source
import template_filters
import version


class TestTemplateFilters(object):

    def verify_rel_datetime_format(self, app):
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

    def verify_filesizeformat(self, app):
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

    def test_filters(self):
        sources = [
            'tests/i18n/code.py',
        ]
        kwargs = {
            'translations_dir': config.TEMP_DIR,
            'mapping': 'tests/i18n/babel.cfg',
            'source': sources,
            'extract_update': True,
            'compile': True,
            'verbose': logging.DEBUG,
            'version': version.__version__,
        }
        args = argparse.Namespace(**kwargs)
        manage.setup_verbosity(args)
        manage.translate_messages(args)

        manage.sh("""
        pybabel init -i {d}/messages.pot -d {d} -l en_US
        pybabel init -i {d}/messages.pot -d {d} -l fr_FR
        """.format(d=config.TEMP_DIR))

        supported = getattr(config, 'SUPPORTED_LOCALES', None)
        try:
            if supported:
                del config.SUPPORTED_LOCALES
            for app in (journalist.app, source.app):
                config.SUPPORTED_LOCALES = ['en_US', 'fr_FR']
                app.config['BABEL_TRANSLATION_DIRECTORIES'] = config.TEMP_DIR
                i18n.setup_app(app)
                self.verify_filesizeformat(app)
                self.verify_rel_datetime_format(app)
        finally:
            if supported:
                config.SUPPORTED_LOCALES = supported

    @classmethod
    def teardown_class(cls):
        reload(journalist)
        reload(source)
