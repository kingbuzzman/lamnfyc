import os
import subprocess
import collections

import lamnfyc.utils
import lamnfyc.context_managers
import lamnfyc.decorators
import lamnfyc.settings


@lamnfyc.decorators.check_installed('bin/redis-server')
def three_two_installer(package, temp):
    with lamnfyc.context_managers.chdir(os.path.join(temp, 'redis-{}'.format(package.version))):
        subprocess.call('make && make PREFIX={} install'.format(lamnfyc.settings.environment_path), shell=True)


class Redis(lamnfyc.utils.TarPacket):
    BASE_PATH = os.path.dirname(os.path.realpath(__file__))


VERSIONS = collections.OrderedDict()
VERSIONS['3.2.3'] = Redis('http://download.redis.io/releases/redis-3.2.3.tar.gz',
                          installer=three_two_installer,
                          md5_signature='138209b54dfc9819e6aea7b9503f8bd3')

for version, item in VERSIONS.iteritems():
    item.name = 'redis'
    item.version = version
