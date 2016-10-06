import functools


def check_installed(path):
    path = path

    def actual_decorator(func):
        @functools.wraps(func)
        def wrapped(*args):
            return func(*args)
        wrapped.path = path
        return wrapped
    return actual_decorator
