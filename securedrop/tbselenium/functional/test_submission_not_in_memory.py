from functional_test import FunctionalTest
import subprocess
from source_navigation_steps import SourceNavigationStepsMixin
import os
import pytest
import getpass
import re


class TestSubmissionNotInMemory(FunctionalTest,
                                SourceNavigationStepsMixin):

    def setup(self):
        self.devnull = open('/dev/null', 'r')
        FunctionalTest.setup(self)

    def teardown(self):
        FunctionalTest.teardown(self)

    def _memory_dump(self, pid):
        core_dump_base_name = '/tmp/core_dump'
        core_dump_file_name = core_dump_base_name + '.' + pid
        try:
            subprocess.call(["sudo", "gcore", "-o",
                            core_dump_base_name, pid], stdout=self.devnull,
                            stderr=self.devnull)
            subprocess.call(["sudo", "chown", getpass.getuser(),
                            core_dump_file_name])
            with open(core_dump_file_name, 'r') as fp:
                return fp.read()
        finally:
            pass
            os.remove(core_dump_file_name)

    def _num_strings_in(self, needle, haystack):
        return sum(1 for _ in re.finditer(re.escape(needle), haystack))

    @pytest.mark.xfail()
    def test_message_is_not_retained_in_memory(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_message()

        source_server_pid = str(self.source_process.pid)

        memory_dump = self._memory_dump(source_server_pid)
        secrets_in_memory = self._num_strings_in(self.secret_message,
                                                 memory_dump)

        assert secrets_in_memory < 1

    @pytest.mark.xfail()
    def test_file_upload_is_not_retained_in_memory(self):
        self._source_visits_source_homepage()
        self._source_chooses_to_submit_documents()
        self._source_continues_to_submit_page()
        self._source_submits_a_file()

        source_server_pid = str(self.source_process.pid)

        memory_dump = self._memory_dump(source_server_pid)
        secrets_in_memory = self._num_strings_in(self.secret_message,
                                                 memory_dump)

        assert secrets_in_memory < 1
