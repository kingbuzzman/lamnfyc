import os
import functools
import logging

import lamnfyc.settings

log = logging.getLogger('lamnfyc')


def check_installed(check_path):
    def check_exists():
        path = os.path.join(lamnfyc.settings.environment_path, check_path)
        if os.path.isfile(path):
            log.debug('{} already exists, skippping'.format(check_path))
            return True
        return False

    def actual_decorator(func):
        @functools.wraps(func)
        def wrapped(*args):
            if not check_exists():
                return func(*args)
        wrapped.installed = check_exists
        return wrapped
    return actual_decorator
