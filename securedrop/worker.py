import logging
import os
from typing import List, Optional

from redis import Redis
from rq.exceptions import InvalidJobOperation, NoSuchJobError
from rq.queue import Queue
from rq.registry import StartedJobRegistry
from rq.worker import Worker, WorkerStatus
from sdconfig import config


def create_queue(name: Optional[str] = None, timeout: int = 3600) -> Queue:
    """
    Create an rq ``Queue`` named ``name`` with default timeout ``timeout``.

    If ``name`` is omitted, ``config.RQ_WORKER_NAME`` is used.
    """
    if name is None:
        name = config.RQ_WORKER_NAME
    q = Queue(name=name, connection=Redis(), default_timeout=timeout)
    return q


def rq_workers(queue: Queue = None) -> List[Worker]:
    """
    Returns the list of current rq ``Worker``s.
    """

    return Worker.all(connection=Redis(), queue=queue)


def worker_for_job(job_id: str) -> Optional[Worker]:
    """
    If the job is being run, return its ``Worker``.
    """
    for worker in rq_workers():
        # If the worker process no longer exists, skip it. From "man 2
        # kill": "If sig is 0, then no signal is sent, but existence
        # and permission checks are still performed; this can be used
        # to check for the existence of a process ID or process group
        # ID that the caller is permitted to signal."
        try:
            os.kill(worker.pid, 0)
        except OSError:
            continue

        # If it's running and working on the given job, return it.
        if worker.state == WorkerStatus.BUSY and job_id == worker.get_current_job_id():
            return worker
    return None


def requeue_interrupted_jobs(queue_name: Optional[str] = None) -> None:
    """
    Requeues jobs found in the given queue's started job registry.

    Only restarts those that aren't already queued or being run.

    When rq starts a job, it records it in the queue's started job
    registry. If the server is rebooted before the job completes, the
    job is not automatically restarted from the information in the
    registry. For tasks like secure deletion of files, this means that
    information thought to be deleted is still present in the case of
    seizure or compromise. We have manage.py tasks to clean such files
    up, but this utility attempts to reduce the need for manual
    intervention by automatically resuming interrupted jobs.

    This function is predicated on a risky assumption: that all jobs
    are idempotent. At time of writing, we use rq for securely
    deleting submission files and hashing submissions for the ETag
    header. Both of these can be safely repeated. If we add rq tasks
    that cannot, this function should be improved to omit those.
    """
    queue = create_queue(queue_name)
    started_job_registry = StartedJobRegistry(queue=queue)

    queued_job_ids = queue.get_job_ids()
    logging.debug("queued jobs: {}".format(queued_job_ids))
    started_job_ids = started_job_registry.get_job_ids()
    logging.debug("started jobs: {}".format(started_job_ids))
    job_ids = [j for j in started_job_ids if j not in queued_job_ids]
    logging.debug("candidate job ids: {}".format(job_ids))

    if not job_ids:
        logging.debug("No interrupted jobs found in started job registry.")

    for job_id in job_ids:
        logging.debug("Considering job %s", job_id)
        try:
            job = started_job_registry.job_class.fetch(job_id, started_job_registry.connection)
        except NoSuchJobError as e:
            logging.error("Could not find details for job %s: %s", job_id, e)
            continue

        logging.debug(
            "Job %s enqueued at %s, started at %s", job_id, job.enqueued_at, job.started_at
        )

        worker = worker_for_job(job_id)
        if worker:
            logging.info(
                "Skipping job %s, which is already being run by worker %s", job_id, worker.key
            )
            continue

        logging.info("Requeuing job %s", job)

        try:
            started_job_registry.remove(job)
        except InvalidJobOperation as e:
            logging.error("Could not remove job %s from started job registry: %s", job, e)
            continue

        try:
            queue.enqueue_job(job)
            logging.debug("Job now enqueued at %s, started at %s", job.enqueued_at, job.started_at)
        except Exception as e:
            logging.error("Could not requeue job %s: %s", job, e)
            continue
