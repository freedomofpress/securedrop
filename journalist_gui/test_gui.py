import unittest
import subprocess
import pexpect
from unittest import mock
from unittest.mock import MagicMock
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QSizePolicy, QInputDialog)
from PyQt5.QtTest import QTest

from journalist_gui.SecureDropUpdater import UpdaterApp, strings, FLAG_LOCATION


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

    def test_window_is_a_fixed_size(self):
        # Verify the size policy is fixed
        expected_sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        assert self.window.sizePolicy() == expected_sizePolicy

        # Verify the maximum and minimum sizes are the same as the current size
        current_size = self.window.size()
        assert self.window.minimumSize() == current_size
        assert self.window.maximumSize() == current_size

    def test_clicking_install_later_exits_the_application(self):
        QTest.mouseClick(self.window.pushButton, Qt.LeftButton)
        self.assertFalse(self.window.isVisible())

    def test_progress_bar_begins_at_zero(self):
        self.assertEqual(self.window.progressBar.value(), 0)

    def test_default_tab(self):
        self.assertEqual(self.window.tabWidget.currentIndex(), 0)

    def test_output_tab(self):

        tab = self.window.tabWidget.tabBar()
        QTest.mouseClick(tab, Qt.LeftButton)
        self.assertEqual(self.window.tabWidget.currentIndex(),
                         self.window.tabWidget.indexOf(self.window.tab_2))

    @mock.patch('subprocess.check_output',
                return_value=b'Python dependencies for securedrop-admin')
    def test_setupThread(self, check_output):
        with mock.patch.object(self.window, "call_tailsconfig",
                               return_value=MagicMock()):
            with mock.patch('builtins.open') as mock_open:
                self.window.setup_thread.run()  # Call run directly

            mock_open.assert_called_once_with(FLAG_LOCATION, 'a')
            self.assertEqual(self.window.update_success, True)
            self.assertEqual(self.window.progressBar.value(), 70)

    @mock.patch('subprocess.check_output',
                return_value=b'Failed to install pip dependencies')
    def test_setupThread_failure(self, check_output):
        with mock.patch.object(self.window, "call_tailsconfig",
                               return_value=MagicMock()):
            with mock.patch('builtins.open') as mock_open:
                self.window.setup_thread.run()  # Call run directly

            mock_open.assert_called_once_with(FLAG_LOCATION, 'a')
            self.assertEqual(self.window.update_success, False)
            self.assertEqual(self.window.progressBar.value(), 0)
            self.assertEqual(self.window.failure_reason,
                             strings.update_failed_generic_reason)

    @mock.patch('subprocess.check_output',
                return_value=b'Signature verification successful')
    def test_updateThread(self, check_output):
        with mock.patch.object(self.window, "setup_thread",
                               return_value=MagicMock()):
            self.window.update_thread.run()  # Call run directly
            self.assertEqual(self.window.update_success, True)
            self.assertEqual(self.window.progressBar.value(), 50)

    @mock.patch('subprocess.check_output',
                side_effect=subprocess.CalledProcessError(
                    1, 'cmd', b'Signature verification failed'))
    def test_updateThread_failure(self, check_output):
        with mock.patch.object(self.window, "setup_thread",
                               return_value=MagicMock()):
            self.window.update_thread.run()  # Call run directly
            self.assertEqual(self.window.update_success, False)
            self.assertEqual(self.window.failure_reason,
                             strings.update_failed_sig_failure)

    @mock.patch('subprocess.check_output',
                side_effect=subprocess.CalledProcessError(
                    1, 'cmd', b'Generic other failure'))
    def test_updateThread_generic_failure(self, check_output):
        with mock.patch.object(self.window, "setup_thread",
                               return_value=MagicMock()):
            self.window.update_thread.run()  # Call run directly
            self.assertEqual(self.window.update_success, False)
            self.assertEqual(self.window.failure_reason,
                             strings.update_failed_generic_reason)

    def test_get_sudo_password_when_password_provided(self):
        expected_password = "password"

        with mock.patch.object(QInputDialog, 'getText',
                               return_value=[expected_password, True]):
            sudo_password = self.window.get_sudo_password()

        self.assertEqual(sudo_password, expected_password)

    def test_get_sudo_password_when_password_not_provided(self):
        test_password = ""

        with mock.patch.object(QInputDialog, 'getText',
                               return_value=[test_password, False]):
            self.assertIsNone(self.window.get_sudo_password())

    @mock.patch('pexpect.spawn')
    def test_tailsconfigThread_no_failures(self, pt):
        child = pt()
        before = MagicMock()

        before.decode.side_effect = ["SUDO: ", "Update successful. failed=0"]
        child.before = before
        child.exitstatus = 0
        with mock.patch('os.remove') as mock_remove:
            self.window.tails_thread.run()

        mock_remove.assert_called_once_with(FLAG_LOCATION)
        self.assertIn("failed=0", self.window.output)
        self.assertEqual(self.window.update_success, True)

    @mock.patch('pexpect.spawn')
    def test_tailsconfigThread_generic_failure(self, pt):
        child = pt()
        before = MagicMock()
        before.decode.side_effect = ["SUDO: ", "failed=10 ERROR!!!!!"]
        child.before = before
        self.window.tails_thread.run()
        self.assertNotIn("failed=0", self.window.output)
        self.assertEqual(self.window.update_success, False)
        self.assertEqual(self.window.failure_reason,
                         strings.tailsconfig_failed_generic_reason)

    @mock.patch('pexpect.spawn')
    def test_tailsconfigThread_sudo_password_is_wrong(self, pt):
        child = pt()
        before = MagicMock()
        before.decode.side_effect = ["some data",
                                     pexpect.exceptions.TIMEOUT(1)]
        child.before = before
        self.window.tails_thread.run()
        self.assertNotIn("failed=0", self.window.output)
        self.assertEqual(self.window.update_success, False)
        self.assertEqual(self.window.failure_reason,
                         strings.tailsconfig_failed_sudo_password)

    @mock.patch('pexpect.spawn')
    def test_tailsconfigThread_some_other_subprocess_error(self, pt):
        child = pt()
        before = MagicMock()
        before.decode.side_effect = subprocess.CalledProcessError(
                                       1, 'cmd', b'Generic other failure')
        child.before = before
        self.window.tails_thread.run()
        self.assertNotIn("failed=0", self.window.output)
        self.assertEqual(self.window.update_success, False)
        self.assertEqual(self.window.failure_reason,
                         strings.tailsconfig_failed_generic_reason)

    def test_tails_status_success(self):
        result = {'status': True, "output": "successful.",
                  'failure_reason': ''}

        with mock.patch('os.remove') as mock_remove:
                    self.window.tails_status(result)

        # We do remove the flag file if the update does finish
        mock_remove.assert_called_once_with(FLAG_LOCATION)
        self.assertEqual(self.window.progressBar.value(), 100)

    def test_tails_status_failure(self):
        result = {'status': False, "output": "successful.",
                  'failure_reason': '42'}

        with mock.patch('os.remove') as mock_remove:
                    self.window.tails_status(result)

        # We do not remove the flag file if the update does not finish
        mock_remove.assert_not_called()
        self.assertEqual(self.window.progressBar.value(), 0)


if __name__ == '__main__':
    unittest.main()
