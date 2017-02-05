# -*- coding: utf-8 -*-
import source
import unittest
import util
from util import PathException


class TestUtil(unittest.TestCase):

    def test_svg_valid(self):
        with source.app.app_context():
            res = util.svg('success_checkmark.svg')
            self.assertIn('<svg', res)

    def test_svg_bad_extension(self):
        with source.app.app_context():
            with self.assertRaises(PathException):
                util.svg('config.py')

    def test_svg_bad_path(self):
        with source.app.app_context():
            with self.assertRaises(PathException):
                util.svg('../../../../etc/hosts')
