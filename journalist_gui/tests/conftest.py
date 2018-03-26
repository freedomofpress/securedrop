import pytest
import sys
from pytestqt import qtbot

from PyQt5.QtWidgets import QApplication

from journalist_gui import SecureDropUpdater


@pytest.fixture(scope='function')
def app():
    app = QApplication(sys.argv)
    return app


@pytest.fixture(scope='function')
def window(app):
    window = SecureDropUpdater.UpdaterApp()
    window.show()
    return window


@pytest.fixture(scope='function')
def gui(qtbot, window, app):
    # Registering the window means it will get cleanly closed after each test.
    qtbot.addWidget(window)
    return qtbot
