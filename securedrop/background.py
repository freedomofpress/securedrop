import threading


def execute(func):
    threading.Thread(target=func).start()
