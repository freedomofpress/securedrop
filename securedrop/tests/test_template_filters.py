# -*- coding: utf-8 -*-
import argparse
import logging
from datetime import datetime, timedelta
import os
import unittest

from flask import session

os.environ['SECUREDROP_ENV'] = 'test'  # noqa
import config
import i18n
import journalist
import manage
import source
import template_filters
import version


class TestTemplateFilters(unittest.TestCase):

    def test_datetimeformat_default_fmt(self):
        result = template_filters.datetimeformat(datetime(2016, 1, 1, 1, 1, 1))
        self.assertEquals("Jan 01, 2016 01:01 AM", result)

    def test_datetimeformat_unusual_fmt(self):
        result = template_filters.datetimeformat(datetime(2016, 1, 1, 1, 1, 1),
                                                 fmt="%b %d %Y")
        self.assertEquals("Jan 01 2016", result)

    def test_relative_timestamp_seconds(self):
        test_time = datetime.utcnow() - timedelta(seconds=5)
        result = template_filters._relative_timestamp(test_time)
        self.assertIn("seconds", result)

    def test_relative_timestamp_one_minute(self):
        test_time = datetime.utcnow() - timedelta(minutes=1)
        result = template_filters._relative_timestamp(test_time)
        self.assertEquals("a minute", result)

    def test_relative_timestamp_minutes(self):
        test_time = datetime.utcnow() - timedelta(minutes=10)
        result = template_filters._relative_timestamp(test_time)
        self.assertEquals("10 minutes", result)

    def test_relative_timestamp_one_hour(self):
        test_time = datetime.utcnow() - timedelta(hours=1)
        result = template_filters._relative_timestamp(test_time)
        self.assertEquals("an hour", result)

    def test_relative_timestamp_hours(self):
        test_time = datetime.utcnow() - timedelta(hours=10)
        result = template_filters._relative_timestamp(test_time)
        self.assertEquals("10 hours", result)

    def test_relative_timestamp_one_day(self):
        test_time = datetime.utcnow() - timedelta(days=1)
        result = template_filters._relative_timestamp(test_time)
        self.assertEquals("a day", result)

    def test_relative_timestamp_days(self):
        test_time = datetime.utcnow() - timedelta(days=4)
        result = template_filters._relative_timestamp(test_time)
        self.assertEquals("4 days", result)

    def test_relative_timestamp_none(self):
        test_time = datetime.utcnow() - timedelta(days=999)
        result = template_filters._relative_timestamp(test_time)
        self.assertEquals(None, result)

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

    def test_filesizeformat(self):
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

        for app in (journalist.app, source.app):
            app.config['BABEL_TRANSLATION_DIRECTORIES'] = config.TEMP_DIR
            i18n.setup_app(app)
            self.verify_filesizeformat(app)

    @classmethod
    def teardown_class(cls):
        reload(journalist)
        reload(source)
