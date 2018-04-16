# -*- coding: utf-8 -*-

from qa_loader import load_data


def test_load_data(journalist_app, config):
    # Use the journalist_app fixture to init the DB
    load_data(config, multiplier=1)
