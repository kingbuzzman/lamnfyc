import logging

log = logging.getLogger('lamnfyc')
log.setLevel(logging.DEBUG)

console = logging.StreamHandler()
# console.setLevel(logging.DEBUG)
console.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
log.addHandler(console)
