#!/usr/bin/python
from PyQt5 import QtGui, QtWidgets
import sys
import subprocess
import os
import pexpect

from journalist_gui import updaterUI, strings


class UpdaterApp(QtWidgets.QMainWindow, updaterUI.Ui_MainWindow):
    def __init__(self, parent=None):
        super(UpdaterApp, self).__init__(parent)
        self.setupUi(self)

        self.window_width = 350
        self.window_collapsed_height = 175
        self.window_full_height = 425

        self.progressBar.setProperty("value", 0)
        self.setWindowTitle(strings.window_title)
        self.setWindowIcon(QtGui.QIcon('./securedrop_icon.png'))
        self.label.setText(strings.update_in_progress)

        # Connect buttons to their functions.
        self.pushButton.setText(strings.install_later_button)
        self.pushButton.clicked.connect(self.close)
        self.pushButton_2.setText(strings.install_update_button)
        self.pushButton_2.clicked.connect(self.update_securedrop)

        # Begin program with output box hidden.
        self.groupBox.toggled.connect(self.expand_or_shrink_output_text_box)
        self.groupBox.setChecked(False)
        self.expand_or_shrink_output_text_box()

    def expand_or_shrink_output_text_box(self):
        # When user toggles the checkbox, expand the output box.
        if self.groupBox.isChecked():
            self.resize(self.window_width, self.window_full_height)
            self.frame.setVisible(True)
        else:
            self.resize(self.window_width, self.window_collapsed_height)
            self.frame.setVisible(False)

    def update_securedrop(self):
        self.progressBar.setProperty("value", 10)
        self.statusbar.showMessage(strings.fetching_update)
        self.progressBar.setProperty("value", 20)
        update_command = ['/home/amnesia/Persistent/securedrop/securedrop-admin',
                          'update']
        try:
            self.output = subprocess.check_output(update_command,
                                                  stderr=subprocess.STDOUT)
            if 'Signature verification failed' in self.output:
                self.update_success = False
                failure_reason = strings.update_failed_sig_failure
            self.update_success = True
        except subprocess.CalledProcessError as e:
            self.output = e.output
            self.update_success = False
            failure_reason = strings.update_failed_generic_reason
        self.progressBar.setProperty("value", 40)
        self.plainTextEdit.setPlainText(self.output.decode('utf-8'))
        self.plainTextEdit.setReadOnly = True

        self.progressBar.setProperty("value", 50)
        failure_reason = self.configure_tails()
        self.progressBar.setProperty("value", 80)

        if self.update_success:
            self.statusbar.showMessage(strings.finished)
            self.progressBar.setProperty("value", 100)
            self.alert_success()
        else:
            self.alert_failure(failure_reason)

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
        error_dialog_box.setText(failure_reason)
        error_dialog_box.setWindowTitle(strings.update_failed_dialog_title)
        error_dialog_box.exec_()
        self.progressBar.setProperty("value", 0)

    def get_sudo_password(self):
        sudo_password, ok_is_pressed = QtWidgets.QInputDialog.getText(
            self, "Tails sudo password", "Tails sudo password:",
            QtWidgets.QLineEdit.Password, "")
        if ok_is_pressed and sudo_password:
            return sudo_password
        else:
            sys.exit(0)

    def configure_tails(self):
        """Run tailsconfig if the signature verified and the update succeeded."""
        tailsconfig_command = '/home/amnesia/Persistent/securedrop/securedrop-admin tailsconfig'
        if self.update_success:
            self.statusbar.showMessage(strings.updating_tails_env)
            # Get sudo password and add an enter key as tailsconfig command
            # expects
            sudo_password = self.get_sudo_password() + '\n'
            try:
                child = pexpect.spawn(tailsconfig_command)
                child.expect('SUDO password:')
                self.output += child.before.decode('utf-8')
                child.sendline(sudo_password)
                child.expect(pexpect.EOF)
                self.output += child.before.decode('utf-8')
                self.plainTextEdit.setPlainText(self.output)

                # For Tailsconfig to be considered a success, we expect no
                # failures in the Ansible output.
                if 'failed=0' not in self.output:
                    self.update_success = False
                    failure_reason = strings.tailsconfig_failed_generic_reason
                    return failure_reason

            except pexpect.exceptions.TIMEOUT:
                self.update_success = False
                failure_reason = strings.tailsconfig_failed_sudo_password
                return failure_reason

            except subprocess.CalledProcessError:
                self.update_success = False
                failure_reason = strings.tailsconfig_failed_generic_reason
                return failure_reason

        return 'Success!'
