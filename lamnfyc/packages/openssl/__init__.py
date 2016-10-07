import os
import collections
import subprocess

import lamnfyc.context_managers
import lamnfyc.settings
import lamnfyc.decorators
import lamnfyc.packages.base


@lamnfyc.decorators.check_installed('lib/libssl.a')
def one_zero_installer(package, temp, env):
    with lamnfyc.context_managers.chdir(os.path.join(temp, 'openssl-{}'.format(package.version))):
        subprocess.call('./Configure darwin64-x86_64-cc --prefix={}'.format(lamnfyc.settings.environment_path),
                        shell=True)
        subprocess.call('make depend', shell=True)
        subprocess.call('make', shell=True)
        subprocess.call('make install', shell=True)


VERSIONS = collections.OrderedDict()
VERSIONS['1.0.2g'] = lamnfyc.packages.base.TarPacket('https://www.openssl.org/source/openssl-1.0.2g.tar.gz',
                                                     installer=one_zero_installer,
                                                     md5_signature='f3c710c045cdee5fd114feb69feba7aa')

for version, item in VERSIONS.iteritems():
    item.name = 'openssl'
    item.version = version
