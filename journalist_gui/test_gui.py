import unittest
import subprocess
import pexpect
from unittest import mock
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QSizePolicy, QInputDialog
from PyQt5.QtTest import QTest

from journalist_gui.SecureDropUpdater import UpdaterApp, strings


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
                return_value=b'Updated to SecureDrop')
    def test_check_out_latest_tag_success(self, check_output):
        self.window.check_out_and_verify_latest_tag()
        self.assertEqual(self.window.update_success, True)
        self.assertEqual(self.window.progressBar.value(), 40)

    @mock.patch('subprocess.check_output',
                return_value=b'Signature verification failed')
    def test_check_out_latest_tag_verification_failure(self, check_output):
        self.window.check_out_and_verify_latest_tag()
        self.assertEqual(self.window.update_success, False)
        self.assertEqual(self.window.failure_reason,
                         strings.update_failed_sig_failure)

    @mock.patch('subprocess.check_output',
                side_effect=subprocess.CalledProcessError(
                    1, 'cmd', 'Generic other failure'))
    def test_check_out_latest_generic_failure(self, check_output):
        self.window.check_out_and_verify_latest_tag()
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
            # If the user does not provide a sudo password, we exit
            # as we cannot update.
            with self.assertRaises(SystemExit):
                self.window.get_sudo_password()

    def test_tailsconfig_no_failures(self):
        self.window.update_success = True
        with mock.patch.object(self.window, 'get_sudo_password',
                               return_value="password"):
            with mock.patch.object(self.window,
                                   'pass_sudo_password_to_tailsconfig',
                                   return_value="failed=0"):
                self.window.configure_tails()

        self.assertIn("failed=0", self.window.output)
        self.assertEqual(self.window.update_success, True)

    def test_tailsconfig_generic_failure(self):
        self.window.update_success = True
        with mock.patch.object(self.window, 'get_sudo_password',
                               return_value="password"):
            with mock.patch.object(self.window,
                                   'pass_sudo_password_to_tailsconfig',
                                   return_value="failed=10 ERROR!!!!!"):
                self.window.configure_tails()

        self.assertNotIn("failed=0", self.window.output)
        self.assertEqual(self.window.update_success, False)
        self.assertEqual(self.window.failure_reason,
                         strings.tailsconfig_failed_generic_reason)

    def test_tailsconfig_sudo_password_is_wrong(self):
        self.window.update_success = True
        with mock.patch.object(self.window, 'get_sudo_password',
                               return_value="password"):
            with mock.patch.object(self.window,
                                   'pass_sudo_password_to_tailsconfig',
                                   side_effect=pexpect.exceptions.TIMEOUT(1)):
                self.window.configure_tails()

        self.assertNotIn("failed=0", self.window.output)
        self.assertEqual(self.window.update_success, False)
        self.assertEqual(self.window.failure_reason,
                         strings.tailsconfig_failed_sudo_password)

    def test_tailsconfig_some_other_subprocess_error(self):
        self.window.update_success = True
        with mock.patch.object(self.window, 'get_sudo_password',
                               return_value="password"):
            with mock.patch.object(self.window,
                                   'pass_sudo_password_to_tailsconfig',
                                   side_effect=subprocess.CalledProcessError(
                                       1, 'cmd', 'Generic other failure')):
                self.window.configure_tails()

        self.assertNotIn("failed=0", self.window.output)
        self.assertEqual(self.window.update_success, False)
        self.assertEqual(self.window.failure_reason,
                         strings.tailsconfig_failed_generic_reason)


if __name__ == '__main__':
    unittest.main()
