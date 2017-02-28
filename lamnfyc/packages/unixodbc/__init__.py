import os
import collections
import subprocess

import lamnfyc.context_managers
import lamnfyc.settings
import lamnfyc.packages.base


def installer(package, temp, env):
    with lamnfyc.context_managers.chdir(os.path.join(temp, 'unixODBC-{}'.format(package.version))):
        command = ('./configure --disable-debug '
                   '--disable-dependency-tracking '
                   '--prefix={} '
                   '--enable-static '
                   '--enable-gui=no && make install')
        subprocess.call(command.format(lamnfyc.settings.environment_path), shell=True)


VERSIONS = collections.OrderedDict()
VERSIONS['2.3.4'] = lamnfyc.packages.base.TarPacket('https://downloads.sourceforge.net/project/unixodbc/unixODBC/2.3.4/unixODBC-2.3.4.tar.gz',  # noqa
                                                      installer=installer,
                                                      sha256_signature='2e1509a96bb18d248bf08ead0d74804957304ff7c6f8b2e5965309c632421e39')  # noqa

for version, item in VERSIONS.iteritems():
    item.name = 'unixodbc'
    item.version = version
