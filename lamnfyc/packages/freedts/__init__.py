import os
import collections
import subprocess
import warnings

import lamnfyc.context_managers
import lamnfyc.settings
import lamnfyc.packages.base


def installer(package, temp, env):
    warnings.warn("This is VERY unteseted")

    with lamnfyc.context_managers.chdir(os.path.join(temp, 'freetds-{}'.format(package.version))):
        command = ('./configure --prefix={0} '
                   '--with-unixodbc={0} '
                   '--mandir={0}/man '
                   '--with-tdsver=7.3 '
                   '--with-openssl={0} && make install')
        subprocess.call(command.format(lamnfyc.settings.environment_path), shell=True)


VERSIONS = collections.OrderedDict()
VERSIONS['1.00.27'] = lamnfyc.packages.base.TarPacket('ftp://ftp.freetds.org/pub/freetds/stable/freetds-1.00.27.tar.gz',  # noqa
                                                      installer=installer,
                                                      md5_signature='093b1e7d1411a84f4264d3111aeead32',
                                                      depends_on=[
                                                          lamnfyc.packages.base.RequiredPacket(name='unixodbc', version='2.3.4'),  # noqa
                                                          lamnfyc.packages.base.RequiredPacket(name='openssl', version='1.0.2g'),  # noqa
                                                      ])

for version, item in VERSIONS.iteritems():
    item.name = 'freedts'
    item.version = version
