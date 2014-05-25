import journalist
import unittest
from mock import patch, ANY, MagicMock

class TestJournalist(unittest.TestCase):

    def setUp(self):
        journalist.request = MagicMock()
        journalist.url_for = MagicMock()
        journalist.redirect = MagicMock()
        journalist.abort = MagicMock()



    @patch("journalist.col_delete")
    def test_col_process_delegates_to_col_delete(self, col_delete):
        journalist.request.form = {"action": "delete"}

        journalist.col_process()

        col_delete.assert_called_with()


    @patch("journalist.col_star")
    def test_col_process_delegates_to_col_star(self, col_star):
        journalist.request.form = {"action": "star"}

        journalist.col_process()

        col_star.assert_called_with()

    @patch("journalist.abort")
    def test_col_process_returns_404_with_bad_action(self, abort):

        journalist.col_process()

        abort.assert_called_with(ANY)

    @patch("journalist.redirect")
    def test_col_star_returns_index_redirect(self, redirect):

        journalist.col_star()

        redirect.assert_called_with(journalist.url_for('index'))