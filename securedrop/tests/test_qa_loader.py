# -*- coding: utf-8 -*-

from qa_loader import QaLoader


def test_load_data(journalist_app, config):
    # Use the journalist_app fixture to init the DB
    QaLoader(config).load()
