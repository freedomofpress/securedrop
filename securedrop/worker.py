import os

from redis import Redis
from rq import Queue

queue_name = 'test' if os.environ.get('SECUREDROP_ENV') == 'test' else 'default'

# `srm` can take a long time on large files, so allow it run for up to an hour
q = Queue(name=queue_name, connection=Redis(), default_timeout=3600)

def enqueue(*args, **kwargs):
    q.enqueue(*args, **kwargs)
