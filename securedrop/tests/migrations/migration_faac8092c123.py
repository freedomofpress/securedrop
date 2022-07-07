# -*- coding: utf-8 -*-


class UpgradeTester:
    """This migration has no upgrade because it is only the enabling of
    pragmas which do not affect database contents.
    """

    def __init__(self, config):
        pass

    def load_data(self):
        pass

    def check_upgrade(self):
        pass


class DowngradeTester:
    """This migration has no downgrade because it is only the enabling of
    pragmas, so we don't need to test the downgrade.
    """

    def __init__(self, config):
        pass

    def load_data(self):
        pass

    def check_downgrade(self):
        pass
