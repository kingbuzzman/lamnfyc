import os
import subprocess
import collections

import lamnfyc.context_managers
import lamnfyc.decorators
import lamnfyc.settings
import lamnfyc.packages.base


@lamnfyc.decorators.check_installed('lib/libreadline.dylib')
def six_three_installer(package, temp):
    with lamnfyc.context_managers.chdir(os.path.join(temp, 'readline-{}'.format(package.version))):
        subprocess.call('./configure --prefix={}'.format(lamnfyc.settings.environment_path), shell=True)
        subprocess.call('make', shell=True)
        subprocess.call('make install', shell=True)


VERSIONS = collections.OrderedDict()
VERSIONS['6.3'] = lamnfyc.packages.base.TarPacket('https://ftpmirror.gnu.org/readline/readline-6.3.tar.gz',
                                                  installer=six_three_installer,
                                                  md5_signature='33c8fb279e981274f485fd91da77e94a')

for version, item in VERSIONS.iteritems():
    item.name = 'readline'
    item.version = version
