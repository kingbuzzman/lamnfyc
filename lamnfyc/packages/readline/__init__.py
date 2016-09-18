import os
import subprocess
import collections

import lamnfyc.utils
import lamnfyc.context_managers
import lamnfyc.settings


def six_three_installer(package, temp):
    with lamnfyc.context_managers.chdir(os.path.join(temp, 'Python-{}'.format(package.version))):
        command = './configure --prefix={} --enable-shared && make && make instal'
        subprocess.call(command.format(lamnfyc.settings.environment_path), shell=True)


VERSIONS = collections.OrderedDict()
VERSIONS['6.3'] = lamnfyc.utils.TarPacket('https://ftpmirror.gnu.org/readline/readline-6.3.tar.gz',
                                          installer=six_three_installer,
                                          md5_signature='83b89587607e3eb65c70d361f13bab43')

for version, item in VERSIONS.iteritems():
    item.name = 'libffi'
    item.version = version
