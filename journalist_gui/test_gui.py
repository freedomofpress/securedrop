import unittest
from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QLineEdit
from PyQt5.QtTest import QTest

import time
from journalist_gui.SecureDropUpdater import UpdaterApp

class AppTestCase(unittest.TestCase):
    def setUp(self):
        qApp = QApplication.instance()
        if qApp is None:
            self.app = QApplication([''])
        else:
            self.app = qApp

class WindowTestCase(AppTestCase):
    def setUp(self):
        super(WindowTestCase, self).setUp()
        self.window = UpdaterApp()
        self.window.show()
        QTest.qWaitForWindowExposed(self.window)

    def test_clicking_install_later_exits_the_application(self):
        QTest.mouseClick(self.window.pushButton, Qt.LeftButton)
        self.assertFalse(self.window.isVisible())

    def test_progress_bar_begins_at_zero(self):
        self.assertEqual(self.window.progressBar.value(), 0)


    def test_output_text_box_is_disabled(self):
        self.assertFalse(self.window.plainTextEdit.isEnabled())
        self.assertFalse(self.window.checkBox.isChecked())


    def test_output_text_box_displayed_when_checkbox_toggled(self):
        
        QTest.mouseClick(self.window.checkBox, Qt.LeftButton)
        self.assertTrue(self.window.plainTextEdit.isEnabled())

        # And clicking again should hide the text box once again
        QTest.mouseClick(self.window.checkBox, Qt.LeftButton)
        self.assertFalse(self.window.plainTextEdit.isEnabled())

if __name__ == '__main__':
    unittest.main()