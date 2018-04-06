#!/usr/bin/python
from PyQt5 import QtGui, QtWidgets
import sys
import subprocess
import pexpect

from journalist_gui import updaterUI, strings, resources_rc  # noqa


class UpdaterApp(QtWidgets.QMainWindow, updaterUI.Ui_MainWindow):
    def __init__(self, parent=None):
        super(UpdaterApp, self).__init__(parent)
        self.setupUi(self)
        self.output = "Beginning update:"

        pixmap = QtGui.QPixmap(":/images/static/securedrop.png")
        self.label_2.setPixmap(pixmap)
        self.label_2.setScaledContents(True)
        self.progressBar.setProperty("value", 0)
        self.setWindowTitle(strings.window_title)
        self.setWindowIcon(QtGui.QIcon(':/images/static/securedrop_icon.png'))
        self.label.setText(strings.update_in_progress)

        # Connect buttons to their functions.
        self.pushButton.setText(strings.install_later_button)
        self.pushButton.clicked.connect(self.close)
        self.pushButton_2.setText(strings.install_update_button)
        self.pushButton_2.clicked.connect(self.update_securedrop)

    def update_securedrop(self):
        self.progressBar.setProperty("value", 10)
        self.check_out_and_verify_latest_tag()
        self.progressBar.setProperty("value", 50)
        if self.update_success:
            self.configure_tails()
        self.progressBar.setProperty("value", 80)

        if self.update_success:
            self.statusbar.showMessage(strings.finished)
            self.progressBar.setProperty("value", 100)
            self.alert_success()
        else:
            self.statusbar.showMessage(self.failure_reason)
            self.alert_failure(self.failure_reason)

    def alert_success(self):
        success_dialog_box = QtWidgets.QMessageBox()
        success_dialog_box.setIcon(QtWidgets.QMessageBox.Information)
        success_dialog_box.setText(strings.finished_dialog_message)
        success_dialog_box.setWindowTitle(strings.finished_dialog_title)
        success_dialog_box.exec_()
        sys.exit(0)

    def alert_failure(self, failure_reason):
        error_dialog_box = QtWidgets.QMessageBox()
        error_dialog_box.setIcon(QtWidgets.QMessageBox.Critical)
        error_dialog_box.setText(self.failure_reason)
        error_dialog_box.setWindowTitle(strings.update_failed_dialog_title)
        error_dialog_box.exec_()
        self.progressBar.setProperty("value", 0)

    def check_out_and_verify_latest_tag(self):
        self.statusbar.showMessage(strings.fetching_update)
        self.progressBar.setProperty("value", 20)
        sdadmin_path = '/home/amnesia/Persistent/securedrop/securedrop-admin'
        update_command = [sdadmin_path, 'update']
        try:
            self.output = subprocess.check_output(
                update_command,
                stderr=subprocess.STDOUT).decode('utf-8')
            if 'Signature verification failed' in self.output:
                self.update_success = False
                self.failure_reason = strings.update_failed_sig_failure
            else:
                self.update_success = True
        except subprocess.CalledProcessError as e:
            self.output = str(e.output)
            self.update_success = False
            self.failure_reason = strings.update_failed_generic_reason
        self.progressBar.setProperty("value", 40)
        self.plainTextEdit.setPlainText(self.output)
        self.plainTextEdit.setReadOnly = True

    def get_sudo_password(self):
        sudo_password, ok_is_pressed = QtWidgets.QInputDialog.getText(
            self, "Tails sudo password", "Tails sudo password:",
            QtWidgets.QLineEdit.Password, "")
        if ok_is_pressed and sudo_password:
            return sudo_password
        else:
            sys.exit(0)

    def pass_sudo_password_to_tailsconfig(self, sudo_password):
        """Pass the sudo password to tailsconfig, and then return
        the output from the screen to the user"""
        tailsconfig_command = ("/home/amnesia/Persistent/"
                               "securedrop/securedrop-admin tailsconfig")

        child = pexpect.spawn(tailsconfig_command)
        child.expect('SUDO password:')
        self.output += child.before.decode('utf-8')
        child.sendline(sudo_password)
        child.expect(pexpect.EOF)
        return child.before.decode('utf-8')

    def configure_tails(self):
        """Run tailsconfig if the signature verified and the
        update succeeded."""
        if self.update_success:
            self.statusbar.showMessage(strings.updating_tails_env)
            # Get sudo password and add an enter key as tailsconfig command
            # expects
            sudo_password = self.get_sudo_password() + '\n'
            try:
                self.output += self.pass_sudo_password_to_tailsconfig(
                    sudo_password
                )
                self.plainTextEdit.setPlainText(self.output)

                # For Tailsconfig to be considered a success, we expect no
                # failures in the Ansible output.
                if 'failed=0' not in self.output:
                    self.update_success = False
                    self.failure_reason = strings.tailsconfig_failed_generic_reason  # noqa

            except pexpect.exceptions.TIMEOUT:
                self.update_success = False
                self.failure_reason = strings.tailsconfig_failed_sudo_password

            except subprocess.CalledProcessError:
                self.update_success = False
                self.failure_reason = strings.tailsconfig_failed_generic_reason
