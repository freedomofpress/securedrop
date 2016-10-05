#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import os
import unittest

import template_filters

# Set environment variable so config.py uses a test environment
os.environ['SECUREDROP_ENV'] = 'test'


class TestTemplateFilters(unittest.TestCase):

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