import os
import logging

__all__ = ('log', 'start_file_log')

log = logging.getLogger('lamnfyc')
log.setLevel(logging.DEBUG)

console = logging.StreamHandler()
console.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
log.addHandler(console)


def start_file_log(log_file_path):
    file_log = logging.FileHandler(os.path.join(log_file_path, 'logs', 'installation.log'))
    file_log.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    file_log.setLevel(logging.DEBUG)
    log.addHandler(file_log)
