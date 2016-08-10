#!/usr/bin/env python
# -*- coding: utf-8 -*-

import manage
import unittest


class TestManagePy(unittest.TestCase):

    def test_parse_args(self):
        # just test that the arg parser is stable
        manage.get_args()
