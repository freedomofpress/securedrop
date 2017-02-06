# -*- coding: utf-8 -*-

from os import path

from flask import current_app


class PathException(Exception):

    """An exception raised by `util.verify` when it encounters a bad path. A path
    can be bad when it is not absolute or not normalized.
    """
    pass


def svg(filename):
    """Safely takes a filename and returns the contents of the file in the
    static directory as a string.
    """

    if not filename.endswith('.svg'):
        raise PathException('File must have .svg extension, but got {}'
                            .format(filename))

    target_path = path.join(path.abspath(current_app.static_folder), 'i', 'svg',
                            filename)
    if not path.isabs(target_path):
        raise PathException('Expected path to SVG to the absolute and '
                            'normalized, but found {}'.format(target_path))

    with open(target_path) as f:
        return f.read()
