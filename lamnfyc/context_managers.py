import os
import contextlib


@contextlib.contextmanager
def chdir(directory):
    old_dir = os.getcwd()
    try:
        os.chdir(directory)
        yield directory
    finally:
        os.chdir(old_dir)
