# -*- coding: utf-8 -*-
"""
Taken from: flask_testing.utils

Flask unittest integration.

:copyright: (c) 2010 by Dan Jacob.
:license: BSD, see LICENSE for more details.
"""


from urllib.parse import urljoin, urlparse

import pytest
from flask import message_flashed, template_rendered

__all__ = ["InstrumentedApp"]


class ContextVariableDoesNotExist(Exception):
    pass


class InstrumentedApp:
    def __init__(self, app):
        self.app = app

    def __enter__(self):
        self.templates = []
        self.flashed_messages = []
        template_rendered.connect(self._add_template)
        message_flashed.connect(self._add_flash_message)
        return self

    def __exit__(self, *nargs):
        if getattr(self, "app", None) is not None:
            del self.app

        del self.templates[:]
        del self.flashed_messages[:]

        template_rendered.disconnect(self._add_template)
        message_flashed.disconnect(self._add_flash_message)

    def _add_flash_message(self, app, message, category):
        self.flashed_messages.append((message, category))

    def _add_template(self, app, template, context):
        if len(self.templates) > 0:
            self.templates = []
        self.templates.append((template, context))

    def assert_message_flashed(self, message, category="message"):
        """
        Checks if a given message was flashed.

        :param message: expected message
        :param category: expected message category
        """
        for _message, _category in self.flashed_messages:
            if _message == message and _category == category:
                return True

        raise AssertionError(
            "Message '{}' in category '{}' wasn't flashed".format(message, category)
        )

    def assert_template_used(self, name, tmpl_name_attribute="name"):
        """
        Checks if a given template is used in the request. If the template
        engine used is not Jinja2, provide ``tmpl_name_attribute`` with a
        value of its `Template` class attribute name which contains the
        provided ``name`` value.

        :param name: template name
        :param tmpl_name_attribute: template engine specific attribute name
        """
        used_templates = []

        for template, context in self.templates:
            if getattr(template, tmpl_name_attribute) == name:
                return True

            used_templates.append(template)

        raise AssertionError(
            "Template {} not used. Templates were used: {}".format(
                name, " ".join(repr(used_templates))
            )
        )

    def get_context_variable(self, name):
        """
        Returns a variable from the context passed to the template.

        Raises a ContextVariableDoesNotExist exception if does not exist in
        context.

        :param name: name of variable
        """
        for template, context in self.templates:
            if name in context:
                return context[name]
        raise ContextVariableDoesNotExist

    def assert_context(self, name, value, message=None):
        """
        Checks if given name exists in the template context
        and equals the given value.

        :versionadded: 0.2
        :param name: name of context variable
        :param value: value to check against
        """

        try:
            assert self.get_context_variable(name) == value, message
        except ContextVariableDoesNotExist:
            pytest.fail(message or "Context variable does not exist: {}".format(name))

    def assert_redirects(self, response, location, message=None):
        """
        Checks if response is an HTTP redirect to the
        given location.

        :param response: Flask response
        :param location: relative URL path to SERVER_NAME or an absolute URL
        """
        parts = urlparse(location)

        if parts.netloc:
            expected_location = location
        else:
            server_name = self.app.config.get("SERVER_NAME") or "localhost.localdomain"
            expected_location = urljoin("http://%s" % server_name, location)

        valid_status_codes = (301, 302, 303, 305, 307)
        valid_status_code_str = ", ".join([str(code) for code in valid_status_codes])
        not_redirect = "HTTP Status {} expected but got {}".format(
            valid_status_code_str, response.status_code
        )
        assert response.status_code in (valid_status_codes, message) or not_redirect
        assert response.location == expected_location, message
