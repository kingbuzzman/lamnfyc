import os
import collections

import lamnfyc.context_managers
import lamnfyc.settings
import lamnfyc.packages.base
import lamnfyc.decorators
import lamnfyc.utils


@lamnfyc.decorators.check_installed('bin/groff')
def one_twenty_two_installer(package, temp, env):
    with lamnfyc.context_managers.chdir(os.path.join(temp, 'groff-{}'.format(package.version))):
        lamnfyc.utils.syscall('./configure --prefix={} --without-x'.format(lamnfyc.settings.environment_path))
        lamnfyc.utils.syscall('make && LC_ALL=C make install')


VERSIONS = collections.OrderedDict()
VERSIONS['1.22.3'] = lamnfyc.packages.base.TarPacket('http://ftp.gnu.org/gnu/groff/groff-1.22.3.tar.gz',
                                                     installer=one_twenty_two_installer,
                                                     md5_signature='cc825fa64bc7306a885f2fb2268d3ec5')

for version, item in VERSIONS.iteritems():
    item.name = 'groff'
    item.version = version
