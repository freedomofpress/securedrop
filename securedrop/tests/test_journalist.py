import journalist
import unittest
from mock import patch, ANY, MagicMock


class TestJournalist(unittest.TestCase):
    def setUp(self):
        journalist.request = MagicMock()
        journalist.url_for = MagicMock()
        journalist.redirect = MagicMock()
        journalist.abort = MagicMock()
        journalist.db_session = MagicMock()
        journalist.get_docs = MagicMock()
        journalist.get_or_else = MagicMock()


    @patch("journalist.col_delete")
    def test_col_process_delegates_to_col_delete(self, col_delete):
        cols_selected = ['source_id']
        self.set_up_request(cols_selected, 'delete')

        journalist.col_process()

        col_delete.assert_called_with(cols_selected)


    @patch("journalist.col_star")
    def test_col_process_delegates_to_col_star(self, col_star):
        cols_selected = ['source_id']
        self.set_up_request(cols_selected, 'star')

        journalist.col_process()

        col_star.assert_called_with(cols_selected)


    @patch("journalist.col_un_star")
    def test_col_process_delegates_to_col_un_star(self, col_un_star):
        cols_selected = ['source_id']
        self.set_up_request(cols_selected, 'un-star')

        journalist.col_process()

        col_un_star.assert_called_with(cols_selected)


    @patch("journalist.abort")
    def test_col_process_returns_404_with_bad_action(self, abort):
        cols_selected = ['source_id']
        self.set_up_request(cols_selected, 'something-random')

        journalist.col_process()

        abort.assert_called_with(ANY)


    @patch("journalist.make_star_true")
    @patch("journalist.db_session")
    def test_col_star_call_db_(self, db_session, make_star_true):
        journalist.col_star(['sid'])

        make_star_true.assert_called_with('sid')

    @patch("journalist.db_session")
    def test_col_un_star_call_db(self, db_session):
        journalist.col_un_star([])

        db_session.commit.assert_called_with()


    def set_up_request(self, cols_selected, action):
        journalist.request.form.__contains__.return_value = True
        journalist.request.form.getlist = MagicMock(return_value=cols_selected)
        journalist.request.form.__getitem__.return_value = action


