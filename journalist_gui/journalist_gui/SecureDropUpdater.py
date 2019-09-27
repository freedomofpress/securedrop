#!/usr/bin/python
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal
import subprocess
import os
import re
import pexpect
import socket
import sys

from journalist_gui import updaterUI, strings, resources_rc  # noqa


FLAG_LOCATION = "/home/amnesia/Persistent/.securedrop/securedrop_update.flag"  # noqa
ESCAPE_POD = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')


def password_is_set():

    pwd_flag = subprocess.check_output(['passwd', '--status']).decode('utf-8').split()[1]

    if pwd_flag == 'NP':
        return False
    return True


def prevent_second_instance(app: QtWidgets.QApplication, name: str) -> None:  # noqa

    # Null byte triggers abstract namespace
    IDENTIFIER = '\0' + name
    ALREADY_BOUND_ERRNO = 98

    app.instance_binding = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        app.instance_binding.bind(IDENTIFIER)
    except OSError as e:
        if e.errno == ALREADY_BOUND_ERRNO:
            err_dialog = QtWidgets.QMessageBox()
            err_dialog.setText(name + strings.app_is_already_running)
            err_dialog.exec()
            sys.exit()
        else:
            raise


class SetupThread(QThread):
    signal = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        QThread.__init__(self)
        self.output = ""
        self.update_success = False
        self.failure_reason = ""

    def run(self):
        sdadmin_path = '/home/amnesia/Persistent/securedrop/securedrop-admin'
        update_command = [sdadmin_path, 'setup']

        # Create flag file to indicate we should resume failed updates on
        # reboot. Don't create the flag if it already exists.
        if not os.path.exists(FLAG_LOCATION):
            open(FLAG_LOCATION, 'a').close()

        try:
            self.output = subprocess.check_output(
                update_command,
                stderr=subprocess.STDOUT).decode('utf-8')
            if 'Failed to install' in self.output:
                self.update_success = False
                self.failure_reason = strings.update_failed_generic_reason
            else:
                self.update_success = True
        except subprocess.CalledProcessError as e:
            self.output += e.output.decode('utf-8')
            self.update_success = False
            self.failure_reason = strings.update_failed_generic_reason
        result = {'status': self.update_success,
                  'output': self.output,
                  'failure_reason': self.failure_reason}
        self.signal.emit(result)


# This thread will handle the ./securedrop-admin update command
class UpdateThread(QThread):
    signal = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        QThread.__init__(self)
        self.output = ""
        self.update_success = False
        self.failure_reason = ""

    def run(self):
        sdadmin_path = '/home/amnesia/Persistent/securedrop/securedrop-admin'
        update_command = [sdadmin_path, 'update']
        try:
            self.output = subprocess.check_output(
                update_command,
                stderr=subprocess.STDOUT).decode('utf-8')
            if "Signature verification successful" in self.output:
                self.update_success = True
            else:
                self.failure_reason = strings.update_failed_generic_reason
        except subprocess.CalledProcessError as e:
            self.update_success = False
            self.output += e.output.decode('utf-8')
            if 'Signature verification failed' in self.output:
                self.failure_reason = strings.update_failed_sig_failure
            else:
                self.failure_reason = strings.update_failed_generic_reason
        result = {'status': self.update_success,
                  'output': self.output,
                  'failure_reason': self.failure_reason}
        self.signal.emit(result)


# This thread will handle the ./securedrop-admin tailsconfig command
class TailsconfigThread(QThread):
    signal = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        QThread.__init__(self)
        self.output = ""
        self.update_success = False
        self.failure_reason = ""
        self.sudo_password = ""

    def run(self):
        tailsconfig_command = ("/home/amnesia/Persistent/"
                               "securedrop/securedrop-admin "
                               "tailsconfig")
        try:
            child = pexpect.spawn(tailsconfig_command)
            child.expect('SUDO password:')
            self.output += child.before.decode('utf-8')
            child.sendline(self.sudo_password)
            child.expect(pexpect.EOF)
            self.output += child.before.decode('utf-8')
            child.close()

            # For Tailsconfig to be considered a success, we expect no
            # failures in the Ansible output.
            if child.exitstatus:
                self.update_success = False
                self.failure_reason = strings.tailsconfig_failed_generic_reason  # noqa
            else:
                self.update_success = True
        except pexpect.exceptions.TIMEOUT:
            self.update_success = False
            self.failure_reason = strings.tailsconfig_failed_sudo_password

        except subprocess.CalledProcessError:
            self.update_success = False
            self.failure_reason = strings.tailsconfig_failed_generic_reason
        result = {'status': self.update_success,
                  'output': ESCAPE_POD.sub('', self.output),
                  'failure_reason': self.failure_reason}
        self.signal.emit(result)


class UpdaterApp(QtWidgets.QMainWindow, updaterUI.Ui_MainWindow):

    def __init__(self, parent=None):
        super(UpdaterApp, self).__init__(parent)
        self.setupUi(self)
        self.statusbar.setSizeGripEnabled(False)
        self.output = strings.initial_text_box
        self.plainTextEdit.setPlainText(self.output)
        self.update_success = False

        pixmap = QtGui.QPixmap(":/images/static/banner.png")
        self.label_2.setPixmap(pixmap)
        self.label_2.setScaledContents(True)

        self.progressBar.setProperty("value", 0)
        self.setWindowTitle(strings.window_title)
        self.setWindowIcon(QtGui.QIcon(':/images/static/securedrop_icon.png'))
        self.label.setText(strings.update_in_progress)

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab),
                                  strings.main_tab)
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2),
                                  strings.output_tab)

        # Connect buttons to their functions.
        self.pushButton.setText(strings.install_later_button)
        self.pushButton.setStyleSheet("""background-color: lightgrey;
                                      min-height: 2em;
                                      border-radius: 10px""")
        self.pushButton.clicked.connect(self.close)
        self.pushButton_2.setText(strings.install_update_button)
        self.pushButton_2.setStyleSheet("""background-color: #E6FFEB;
                                        min-height: 2em;
                                        border-radius: 10px;""")
        self.pushButton_2.clicked.connect(self.update_securedrop)
        self.update_thread = UpdateThread()
        self.update_thread.signal.connect(self.update_status)
        self.tails_thread = TailsconfigThread()
        self.tails_thread.signal.connect(self.tails_status)
        self.setup_thread = SetupThread()
        self.setup_thread.signal.connect(self.setup_status)

    # At the end of this function, we will try to do tailsconfig.
    # A new slot will handle tailsconfig output
    def setup_status(self, result):
        "This is the slot for setup thread"
        self.output += result['output']
        self.update_success = result['status']
        self.failure_reason = result['failure_reason']
        self.progressBar.setProperty("value", 60)
        self.plainTextEdit.setPlainText(self.output)
        self.plainTextEdit.setReadOnly = True
        if not self.update_success:  # Failed to do setup
            self.pushButton.setEnabled(True)
            self.pushButton_2.setEnabled(True)
            self.update_status_bar_and_output(self.failure_reason)
            self.progressBar.setProperty("value", 0)
            self.alert_failure(self.failure_reason)
            return
        self.progressBar.setProperty("value", 70)
        self.call_tailsconfig()

    # This will update the output text after the git commands.
    def update_status(self, result):
        "This is the slot for update thread"
        self.output += result['output']
        self.update_success = result['status']
        self.failure_reason = result['failure_reason']
        self.progressBar.setProperty("value", 40)
        self.plainTextEdit.setPlainText(self.output)
        self.plainTextEdit.setReadOnly = True
        if not self.update_success:  # Failed to do update
            self.pushButton.setEnabled(True)
            self.pushButton_2.setEnabled(True)
            self.update_status_bar_and_output(self.failure_reason)
            self.progressBar.setProperty("value", 0)
            self.alert_failure(self.failure_reason)
            return
        self.progressBar.setProperty("value", 50)
        self.update_status_bar_and_output(strings.doing_setup)
        self.setup_thread.start()

    def update_status_bar_and_output(self, status_message):
        """This method updates the status bar and the output window with the
        status_message."""
        self.statusbar.showMessage(status_message)
        self.output += status_message + '\n'
        self.plainTextEdit.setPlainText(self.output)

    def call_tailsconfig(self):
        # Now let us work on tailsconfig part
        if self.update_success:
            # Get sudo password and add an enter key as tailsconfig command
            # expects
            sudo_password = self.get_sudo_password()
            if not sudo_password:
                self.update_success = False
                self.failure_reason = strings.missing_sudo_password
                self.on_failure()
                return
            self.tails_thread.sudo_password = sudo_password + '\n'
            self.update_status_bar_and_output(strings.updating_tails_env)
            self.tails_thread.start()
        else:
            self.on_failure()

    def tails_status(self, result):
        "This is the slot for Tailsconfig thread"
        self.output += result['output']
        self.update_success = result['status']
        self.failure_reason = result['failure_reason']
        self.plainTextEdit.setPlainText(self.output)
        self.progressBar.setProperty("value", 80)
        if self.update_success:
            # Remove flag file indicating an update is in progress
            os.remove(FLAG_LOCATION)
            self.update_status_bar_and_output(strings.finished)
            self.progressBar.setProperty("value", 100)
            self.alert_success()
        else:
            self.on_failure()

    def on_failure(self):
        self.update_status_bar_and_output(self.failure_reason)
        self.alert_failure(self.failure_reason)
        # Now everything is done, enable the button.
        self.pushButton.setEnabled(True)
        self.pushButton_2.setEnabled(True)
        self.progressBar.setProperty("value", 0)

    def update_securedrop(self):
        if password_is_set():
            self.pushButton_2.setEnabled(False)
            self.pushButton.setEnabled(False)
            self.progressBar.setProperty("value", 10)
            self.update_status_bar_and_output(strings.fetching_update)
            self.update_thread.start()
        else:
            self.pushButton_2.setEnabled(False)
            pwd_err_dialog = QtWidgets.QMessageBox()
            pwd_err_dialog.setText(strings.no_password_set_message)
            pwd_err_dialog.exec()

    def alert_success(self):
        self.success_dialog = QtWidgets.QMessageBox()
        self.success_dialog.setIcon(QtWidgets.QMessageBox.Information)
        self.success_dialog.setText(strings.finished_dialog_message)
        self.success_dialog.setWindowTitle(strings.finished_dialog_title)
        self.success_dialog.show()

    def alert_failure(self, failure_reason):
        self.error_dialog = QtWidgets.QMessageBox()
        self.error_dialog.setIcon(QtWidgets.QMessageBox.Critical)
        self.error_dialog.setText(self.failure_reason)
        self.error_dialog.setWindowTitle(strings.update_failed_dialog_title)
        self.error_dialog.show()

    def get_sudo_password(self):
        sudo_password, ok_is_pressed = QtWidgets.QInputDialog.getText(
            self, "Tails Administrator password", strings.sudo_password_text,
            QtWidgets.QLineEdit.Password, "")
        if ok_is_pressed and sudo_password:
            return sudo_password
        else:
            return None
