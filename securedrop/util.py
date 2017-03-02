# -*- coding: utf-8 -*-

from os import path


class PathException(Exception):

    """An exception raised by `util.verify` when it encounters a bad path. A path
    can be bad when it is not absolute or not normalized.
    """
    pass
