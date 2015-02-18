import unittest
import journalist
from mock import patch, ANY, MagicMock

class TestJournalist(unittest.TestCase):

    def setUp(self):
        journalist.logged_in = MagicMock()
        journalist.make_star_true = MagicMock()
        journalist.db_session = MagicMock()
        journalist.url_for = MagicMock()
        journalist.redirect = MagicMock()
        journalist.get_one_or_else = MagicMock()

    @patch('journalist.url_for')
    @patch('journalist.redirect')
    def test_add_star_renders_template(self, redirect, url_for):
        redirect_template = journalist.add_star('sid')

        self.assertEqual(redirect_template, redirect(url_for('index')))

    @patch('journalist.db_session')
    def test_add_star_makes_commits(self, db_session):
        journalist.add_star('sid')

        db_session.commit.assert_called_with()

    @patch('journalist.make_star_true')
    def test_single_delegates_to_make_star_true(self, make_star_true):
        sid = 'sid'

        journalist.add_star(sid)

        make_star_true.assert_called_with(sid)


    @patch('journalist.url_for')
    @patch('journalist.redirect')
    def test_remove_star_renders_template(self, redirect, url_for):
        redirect_template = journalist.remove_star('sid')

        self.assertEqual(redirect_template, redirect(url_for('index')))

    @patch('journalist.db_session')
    def test_remove_star_makes_commits(self, db_session):
        journalist.remove_star('sid')

        db_session.commit.assert_called_with()

    @patch('journalist.make_star_false')
    def test_remove_star_delegates_to_make_star_false(self, make_star_false):
        sid = 'sid'

        journalist.remove_star(sid)

        make_star_false.assert_called_with(sid)

    @classmethod
    def tearDownClass(cls):
        # Reset the module variables that were changed to mocks so we don't
        # break other tests
        reload(journalist)

