import journalist
import unittest
from db import Source, SourceStar
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
        journalist.request.form = {"action": "delete"}

        journalist.col_process()

        col_delete.assert_called_with()


    @patch("journalist.col_star")
    def test_col_process_delegates_to_col_star(self, col_star):
        journalist.request.form = {"action": "star"}

        journalist.col_process()

        col_star.assert_called_with()


    @patch("journalist.col_un_star")
    def test_col_star_returns_index_redirect(self, col_un_star):
        journalist.request.form = {"action": "un-star"}

        journalist.col_process()

        col_un_star.assert_called_with()


    @patch("journalist.abort")
    def test_col_process_returns_404_with_bad_action(self, abort):
        journalist.col_process()

        abort.assert_called_with(ANY)


    @patch("journalist.abort")
    def test_col_process_returns_404_with_bad_action(self, abort):
        journalist.col_process()

        abort.assert_called_with(ANY)


    @patch("journalist.db_session")
    def test_col_star_call_db_(self, db_session):
        source = Source("source_id")
        source_star = SourceStar(source=source, starred=True)
        self.set_up_journalist(source, source_star)
        journalist.col_star()

        db_session.add.assert_called_with(source_star)

    @patch("journalist.db_session")
    def test_col_un_star_call_db(self, db_session):
        source = Source("source_id")
        source_star = SourceStar(source=source, starred=False)
        source.star = source_star

        self.set_up_journalist(source, source_star)

        journalist.col_un_star()

        db_session.commit.assert_called_with()


    def set_up_journalist(self, source, source_star):
        journalist.get_one_or_else = MagicMock(return_value=source_star)
        journalist.get_source = MagicMock(return_value=source)
        journalist.request.form.__contains__.return_value = True
        journalist.request.form.getlist = MagicMock(return_value=['source_id'])