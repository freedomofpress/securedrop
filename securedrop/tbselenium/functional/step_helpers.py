import os
from os.path import abspath, dirname, join, realpath
import inspect
import traceback

LOG_DIR = abspath(join(dirname(realpath(__file__)), '..', 'log'))
screenshots_enabled = os.environ.get('SCREENSHOTS_ENABLED')


# screenshots is a decorator that records an image before and after
# the steps described in this file
def screenshots(f):
    def wrapper(*args, **kwargs):
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)

        locals = calframe[1][0].f_locals
        if "testfunction" in locals:
            fun = calframe[1][0].f_locals["testfunction"]
            class_name = fun.__self__.__class__.__name__
        else:
            class_name = calframe[1][0].f_locals["self"].__class__.__name__

        stack = [x for x in traceback.extract_stack()
                 if '/functional' in x[0]]
        path = ('-'.join([stack[0][0].split('/')[-1], class_name] +
                         [x[2] for x in stack if x[2] is not 'wrapper']))
        if screenshots_enabled:
            image_path = join(LOG_DIR, '%s-before.png' % path)
            args[0].driver.save_screenshot(image_path)
        result = f(*args, **kwargs)
        if screenshots_enabled:
            image_path = join(LOG_DIR, '%s-after.png' % path)
            args[0].driver.save_screenshot(image_path)
        return result
    return wrapper
