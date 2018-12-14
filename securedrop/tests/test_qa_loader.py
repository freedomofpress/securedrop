# -*- coding: utf-8 -*-

from qa_loader import QaLoader


def test_load_data(journalist_app, journalist_config):
    # Use the journalist_app fixture to init the DB
    QaLoader(journalist_config, multiplier=1).load()
