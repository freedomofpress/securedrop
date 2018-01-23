# -*- coding: utf-8 -*-
from . import journalist_navigation_steps
from . import functional_test


class TestMakeAccountChanges(
        functional_test.FunctionalTest,
        journalist_navigation_steps.JournalistNavigationStepsMixin):

    def test_admin_edit_account_html_template_rendering(self):
        """The edit_account.html template is used both when an admin is editing
        a user's account, and when a user is editing their own account. While
        there is no security risk in doing so, we do want to ensure the UX is
        as expected: that only the elements that belong in a particular view
        are exposed there."""
        self._admin_logs_in()
        self._admin_visits_admin_interface()
        # Admin view of admin user
        self._edit_user(self.admin, True)
        self._admin_visits_admin_interface()
        self._admin_adds_a_user()
        # Admin view of non-admin user
        self._edit_user(self.new_user['username'])
        # User view of self
        self._edit_account()
        self._logout()
