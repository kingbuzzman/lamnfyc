import os
import subprocess
import collections

import lamnfyc.packages.base
import lamnfyc.context_managers
import lamnfyc.decorators
import lamnfyc.settings


@lamnfyc.decorators.check_installed('bin/redis-server')
def three_two_installer(package, temp):
    with lamnfyc.context_managers.chdir(os.path.join(temp, 'redis-{}'.format(package.version))):
        subprocess.call('make && make PREFIX={} install'.format(lamnfyc.settings.environment_path), shell=True)


class RedisPackage(lamnfyc.packages.base.TarPacket):
    BASE_PATH = os.path.dirname(os.path.realpath(__file__))

    # attributed to the environment if not there
    ENVIRONMENT_VARIABLES = (
        lamnfyc.packages.base.required_if(('REDIS_HOST', '127.0.0.1',), lambda options: not options.unix_sockets),
        lamnfyc.packages.base.required_if(('REDIS_PORT', '6379',), lambda options: not options.unix_sockets),
        lamnfyc.packages.base.required_if(('REDIS_SOCK', '$VIRTUAL_ENV/run/redis.sock',),
                                          lambda options: options.unix_sockets),
        ('REDIS_PID', '$VIRTUAL_ENV/run/redis.pid',),
    )

    def __init__(self, *args, **kwargs):
        super(RedisPackage, self).__init__(*args, **kwargs)

        self.options.unix_sockets = False

    def init_options(self, options):
        self.options.unix_sockets = options.pop('unix_sockets', self.options.unix_sockets)


VERSIONS = collections.OrderedDict()
VERSIONS['3.2.3'] = RedisPackage('http://download.redis.io/releases/redis-3.2.3.tar.gz',
                                 installer=three_two_installer,
                                 md5_signature='138209b54dfc9819e6aea7b9503f8bd3')
VERSIONS['3.2.0'] = RedisPackage('http://download.redis.io/releases/redis-3.2.0.tar.gz',
                                 installer=three_two_installer,
                                 md5_signature='9ec99ff912f35946fdb56fe273140483')

for version, item in VERSIONS.iteritems():
    item.name = 'redis'
    item.version = version
