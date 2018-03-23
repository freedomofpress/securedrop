import pytest
import sys

from PyQt5.QtWidgets import QApplication

from journalist_gui import SecureDropUpdater


@pytest.fixture(scope='function')
def gui():
    """Creates a new PyQt GUI for a test."""
    app = QApplication(sys.argv)
    app = SecureDropUpdater.UpdaterApp()
    return app
