from threading import Thread


def asynchronous(f):               # type: ignore
    """
    Wraps a
    """
    def wrapper(*args, **kwargs):  # type: ignore
        thread = Thread(target=f, args=args, kwargs=kwargs)
        thread.start()
    return wrapper
