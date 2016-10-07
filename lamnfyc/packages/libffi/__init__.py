import os
import collections
import subprocess

import lamnfyc.context_managers
import lamnfyc.settings
import lamnfyc.packages.base


def three_two_installer(package, temp, env):
    with lamnfyc.context_managers.chdir(os.path.join(temp, 'libffi-{}'.format(package.version))):
        command = './configure --prefix={} --enable-shared && make && make instal'
        subprocess.call(command.format(lamnfyc.settings.environment_path), shell=True)


VERSIONS = collections.OrderedDict()
VERSIONS['3.2.1'] = lamnfyc.packages.base.TarPacket('ftp://sourceware.org/pub/libffi/libffi-3.2.1.tar.gz',
                                                    installer=three_two_installer,
                                                    md5_signature='83b89587607e3eb65c70d361f13bab43')

for version, item in VERSIONS.iteritems():
    item.name = 'libffi'
    item.version = version
