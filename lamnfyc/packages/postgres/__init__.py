import os
import subprocess
import distutils.dir_util
import collections

import lamnfyc.utils
import lamnfyc.context_managers
import lamnfyc.settings
import lamnfyc.decorators


@lamnfyc.decorators.check_installed('bin/postgres')
def installer(package, temp):
    command = '''LDFLAGS="-L{path}/lib"
                 LD_LIBRARY_PATH={path}/lib
                 CPPFLAGS="-I{path}/include -I{path}/ssl" ./configure --prefix={path}'''
    with lamnfyc.context_managers.chdir(os.path.join(temp, 'postgresql-{}'.format(package.version))):
        subprocess.call(command.format(path=lamnfyc.settings.environment_path), shell=True)
        subprocess.call('make && make install'.format(lamnfyc.settings.environment_path), shell=True)


class PostgresPackage(lamnfyc.packages.base.TarPacket):
    BASE_PATH = os.path.dirname(os.path.realpath(__file__))

    def __init__(self, *args, **kwargs):
        super(PostgresPackage, self).__init__(*args, **kwargs)

        self.options.unix_sockets = None

    def init_options(self, options):
        self.options.unix_sockets = options.pop('unix_sockets', True)


VERSIONS = collections.OrderedDict()
VERSIONS['9.3.9'] = PostgresPackage('https://ftp.postgresql.org/pub/source/v9.3.9/postgresql-9.3.9.tar.bz2',
                                    installer=installer, sha256_signature='f73bd0ec2028511732430beb22414a022d2114231366e8cbe78c149793910549',  # noqa
                                    depends_on=[
                                        lamnfyc.packages.base.RequiredPacket(name='readline', version='6.3'),
                                        lamnfyc.packages.base.RequiredPacket(name='openssl', version='1.0.2g'),
                                    ])

for version, item in VERSIONS.iteritems():
    item.name = 'postgres'
    item.version = version
