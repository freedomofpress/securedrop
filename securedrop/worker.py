from redis import Redis
from rq import Queue


class RqWorkerQueue(object):

    '''
    A reference to a `rq` worker queue.

    Configuration:
        `RQ_WORKER_NAME`: Name of the `rq` worker.
    '''

    __EXT_NAME = 'rq-worker-queue'

    def __init__(self, app=None):
        self.__app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.__app = app
        self.__app.config.setdefault('RQ_WORKER_NAME', 'default')

        try:
            # check for presence of existing extension dict
            self.__app.extensions
        except AttributeError:
            self.__app.extensions = {}

        queue_name = self.__app.config['RQ_WORKER_NAME']
        queue = Queue(name=queue_name, connection=Redis(), default_timeout=3600)
        self.__app.extensions[self.__EXT_NAME] = queue

    def enqueue(self, *nargs, **kwargs):
        queue = self.__app.extensions[self.__EXT_NAME]
        return queue.enqueue(*nargs, **kwargs)


rq_worker_queue = RqWorkerQueue()
