import collections

import lamnfyc.context_managers
import lamnfyc.settings
import lamnfyc.utils


def one_zero_installer(package, temp):
    pass


VERSIONS = collections.OrderedDict()
VERSIONS['1.0.2g'] = lamnfyc.utils.TarPacket('https://www.openssl.org/source/openssl-1.0.2g.tar.gz',
                                             installer=one_zero_installer,
                                             md5_signature='f3c710c045cdee5fd114feb69feba7aa')

for version, item in VERSIONS.iteritems():
    item.name = 'openssl'
    item.version = version
