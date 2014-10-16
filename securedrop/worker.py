import os

from redis import Redis
from rq import Queue

queue_name = 'test' if os.environ.get('SECUREDROP_ENV') == 'test' else 'default'

q = Queue(name=queue_name, connection=Redis())

def enqueue(*args, **kwargs):
    q.enqueue(*args, **kwargs)
