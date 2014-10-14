from redis import Redis
from rq import Queue

q = Queue(connection=Redis())

def enqueue(*args, **kwargs):
    q.enqueue(*args, **kwargs)
