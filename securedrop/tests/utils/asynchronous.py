# -*- coding: utf-8 -*-
"""Testing utilites to block on and react to the success, failure, or
timeout of asynchronous processes.
"""
import time

# This is an arbitarily defined value in the SD codebase and not something from rqworker
REDIS_SUCCESS_RETURN_VALUE = "success"


def wait_for_redis_worker(job, timeout=60):
    """Raise an error if the Redis job doesn't complete successfully
    before a timeout.

    :param rq.job.Job job: A Redis job to wait for.

    :param int timeout: Seconds to wait for the job to finish.

    :raises: An :exc:`AssertionError`.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if job.result == REDIS_SUCCESS_RETURN_VALUE:
            return
        elif job.result not in (None, REDIS_SUCCESS_RETURN_VALUE):
            assert False, "Redis worker failed!"
        time.sleep(0.1)
    assert False, "Redis worker timed out!"


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
