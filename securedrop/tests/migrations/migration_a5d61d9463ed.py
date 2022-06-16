class UpgradeTester:
    def __init__(self, config):
        """This function MUST accept an argument named `config`.
        You will likely want to save a reference to the config in your
        class so you can access the database later.
        """
        self.config = config

    def load_data(self):
        """This function loads data into the database and filesystem. It is
        executed before the upgrade.
        """
        pass

    def check_upgrade(self):
        """This function is run after the upgrade and verifies the state
        of the database or filesystem. It MUST raise an exception if the
        check fails.
        """
        pass


class DowngradeTester:
    def __init__(self, config):
        """This function MUST accept an argument named `config`.
        You will likely want to save a reference to the config in your
        class so you can access the database later.
        """
        self.config = config

    def load_data(self):
        """This function loads data into the database and filesystem. It is
        executed before the downgrade.
        """
        pass

    def check_downgrade(self):
        """This function is run after the downgrade and verifies the state
        of the database or filesystem. It MUST raise an exception if the
        check fails.
        """
        pass
