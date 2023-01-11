"""Testing utilities to block on and react to the success, failure, or
timeout of asynchronous processes.
"""
import time


def wait_for_assertion(assertion_expression, timeout=10):
    """Calls an assertion_expression repeatedly, until the assertion
    passes or a timeout is reached.

    :param assertion_expression: An assertion expression. Generally
                                 a call to a
                                 :class:`unittest.TestCase` method.

    :param int timeout: Seconds to wait for the function to return.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            return assertion_expression()
        except AssertionError:
            time.sleep(0.1)
    # one more try, which will raise any errors if they are outstanding
    return assertion_expression()
