# -*- coding: utf-8 -*-
from unittest import TestCase

from functional_test import FunctionalTest
from journalist_navigation_steps import JournalistNavigationStepsMixin
from step_helpers import screenshots


class MakeAccountChanges(FunctionalTest, JournalistNavigationStepsMixin,
                         TestCase):
    @screenshots
    def test_admin_edit_account_html_template_rendering(self):
        """The edit_account.html template is used both when an admin is editing
        a user's account, and when a user is editing their own account. While
        there is no security risk in doing so, we do want to ensure the UX is
        as expected: that only the elements that belong in a particular view
        are exposed there."""
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        # Admin view of admin user
        self._edit_user('admin')
        self._admin_visits_admin_interface()
        self._admin_adds_a_user()
        # Admin view of non-admin user
        self._edit_user('dellsberg')
        # User view of self
        self._edit_account()
        self._logout()
