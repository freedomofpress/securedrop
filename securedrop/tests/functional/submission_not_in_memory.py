from unittest import TestCase
from functional_test import FunctionalTest
import subprocess
import tempfile
from source_navigation_steps import SourceNavigationSteps
import os
import getpass

class SubmissionNotInMemoryTest(TestCase, FunctionalTest, SourceNavigationSteps):

    def setUp(self):
        FunctionalTest.setUp(self)

    def tearDown(self):
        FunctionalTest.tearDown(self)

    def _memory_dump(self, pid):
        core_dump_base_name = '/tmp/core_dump'
        core_dump_file_name = core_dump_base_name + '.' + pid
        try:
            subprocess.call(["sudo", "gcore", "-o", core_dump_base_name, pid])
            subprocess.call(["sudo", "chown", getpass.getuser(), core_dump_file_name])
            with open(core_dump_file_name, 'r') as fp:
                return fp.read()
        finally:
            os.remove(core_dump_file_name)

    def test_message_is_not_retained_in_memory(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_message()

        source_server_pid = str(self.source_process.pid)

        self.assertFalse(self.secret_message in self._memory_dump(source_server_pid))

    def test_file_upload_is_not_retained_in_memory(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()

        source_server_pid = str(self.source_process.pid)

        self.assertFalse(self.secret_message in self._memory_dump(source_server_pid))

