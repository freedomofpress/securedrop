import sys
from unittest import mock

from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore

from journalist_gui.SecureDropUpdater import UpdaterApp



def test_progress_bar_begins_at_zero(app, window, gui):
    assert window.progressBar.value() == 0


def test_output_text_box_not_initially_displayed(app, window, gui):
    assert window.frame.isVisible() == False
    assert window.plainTextEdit.isVisible() == False
    assert window.groupBox.isChecked() == False


def test_output_text_box_displayed_when_checkbox_toggled(app, window, gui):
    gui.mouseClick(window.groupBox, QtCore.Qt.LeftButton)
    assert window.plainTextEdit.isVisible() == True

    # And clicking again should hide the text box once again
    gui.mouseClick(window.groupBox, QtCore.Qt.LeftButton)
    assert window.plainTextEdit.isVisible() == False


def test_clicking_install_later_exits_the_application(app, window, gui):
    with mock.patch.object(UpdaterApp, 'close'):
        gui.mouseClick(window.pushButton, QtCore.Qt.LeftButton)
        assert UpdaterApp.close.call_count == 1
