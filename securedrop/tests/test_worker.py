import logging
import os
import signal
import subprocess
import time

import worker
from rq.worker import WorkerStatus


def layabout():
    """
    Function that just sleeps for an hour.
    """
    time.sleep(3600)


def start_rq_worker(config, queue_name=None):
    """
    Launches an rq worker process.
    """
    if queue_name is None:
        queue_name = config.RQ_WORKER_NAME
    return subprocess.Popen(
        [
            "/opt/venvs/securedrop-app-code/bin/rqworker",
            "--path",
            config.SECUREDROP_ROOT,
            queue_name,
        ],
        preexec_fn=os.setsid,
    )


def test_no_interrupted_jobs(caplog):
    """
    Tests requeue_interrupted_jobs when there are no interrupted jobs.
    """
    caplog.set_level(logging.DEBUG)

    q = worker.create_queue()
    try:
        assert len(q.get_job_ids()) == 0
        worker.requeue_interrupted_jobs()
        assert "No interrupted jobs found in started job registry." in caplog.text
    finally:
        q.delete()


def test_job_interruption(config, caplog):
    """
    Tests that a job is requeued unless it is already being run.
    """
    caplog.set_level(logging.DEBUG)

    queue_name = "test_job_interruption"
    q = worker_process = None
    try:
        q = worker.create_queue(queue_name)

        # submit a job that sleeps for an hour
        job = q.enqueue(layabout)
        assert len(q.get_job_ids()) == 1

        # launch worker processes
        worker_process = start_rq_worker(config, queue_name)

        i = 0
        while i < 20:
            if len(worker.rq_workers(q)) == 1:
                break
            time.sleep(0.1)

        assert len(worker.rq_workers(q)) == 1

        i = 0
        while i < 20:
            w = worker.worker_for_job(job.id)
            if w:
                break
            i += 1
            time.sleep(0.1)
        assert w is not None

        # the running job should not be requeued
        worker.requeue_interrupted_jobs(queue_name)
        skipped = "Skipping job {}, which is already being run by worker {}".format(job.id, w.key)
        assert skipped in caplog.text

        # kill the process group, to kill the worker and its workhorse
        os.killpg(worker_process.pid, signal.SIGKILL)
        worker_process.wait()
        caplog.clear()

        # after killing the worker, the interrupted job should be requeued
        worker.requeue_interrupted_jobs(queue_name)
        print(caplog.text)
        assert "Requeuing job {}".format(job) in caplog.text
        assert len(q.get_job_ids()) == 1
    finally:
        q.delete()
        if worker_process:
            try:
                os.killpg(worker_process.pid, 0)
                os.killpg(worker_process.pid, signal.SIGKILL)
            except OSError:
                logging.debug("worker_process already gone.")


def test_worker_for_job(config):
    """
    Tests that worker_for_job works when there are multiple workers.
    """

    queue_name = "test_worker_for_job"
    q = worker_process = second_process = None
    try:
        q = worker.create_queue(queue_name)
        assert len(worker.rq_workers(q)) == 0

        # launch worker processes
        worker_process = start_rq_worker(config, queue_name)
        second_process = start_rq_worker(config, queue_name)

        i = 0
        while i < 20:
            if len(worker.rq_workers(q)) == 2:
                break
            time.sleep(0.1)

        assert len(worker.rq_workers(q)) == 2

        worker.rq_workers(q)[0].set_state(WorkerStatus.SUSPENDED)

        logging.debug(
            [
                "{}: state={}, job={}".format(w.pid, w.get_state(), w.get_current_job_id())
                for w in worker.rq_workers(q)
            ]
        )

        # submit a job that sleeps for an hour
        job = q.enqueue(layabout)

        i = 0
        while i < 20:
            w = worker.worker_for_job(job.id)
            if w:
                break
            i += 1
            time.sleep(0.1)
        assert w is not None

    finally:
        q.delete()
        if worker_process:
            try:
                os.killpg(worker_process.pid, 0)
                os.killpg(worker_process.pid, signal.SIGKILL)
            except OSError:
                logging.debug("worker_process already gone.")

        if second_process:
            try:
                os.killpg(second_process.pid, 0)
                os.killpg(second_process.pid, signal.SIGKILL)
            except OSError:
                logging.debug("second_process already gone.")
