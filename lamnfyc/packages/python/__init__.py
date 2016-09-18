import os
import subprocess
import collections

import lamnfyc.utils
import lamnfyc.context_managers
import lamnfyc.settings


def two_seven_installer(package, temp):
    with lamnfyc.context_managers.chdir(os.path.join(temp, 'Python-{}'.format(package.version))):
        subprocess.call('./configure --prefix={} '  # '--enable-shared '
                        '&& make && make instal'.format(lamnfyc.settings.environment_path), shell=True)


def three_five_installer():
    pass


VERSIONS = collections.OrderedDict()
VERSIONS['3.5.0'] = lamnfyc.utils.TarPacket('https://www.python.org/ftp/python/3.5.0/Python-3.5.0.tar.xz',
                                            installer=three_five_installer,
                                            md5_signature='d149d2812f10cbe04c042232e7964171',
                                            depends_on=[
                                                lamnfyc.utils.RequiredPacket(name='readline', version='6.3'),
                                                lamnfyc.utils.RequiredPacket(name='openssl', version='1.0.2g'),
                                            ])

VERSIONS['2.7.12'] = lamnfyc.utils.TarPacket('https://www.python.org/ftp/python/2.7.12/Python-2.7.12.tar.xz',
                                             installer=two_seven_installer,
                                             md5_signature='57dffcee9cee8bb2ab5f82af1d8e9a69',
                                             depends_on=[
                                                 lamnfyc.utils.RequiredPacket(name='libffi', version='3.2.1'),
                                                 lamnfyc.utils.RequiredPacket(name='openssl', version='1.0.2g'),
                                             ])

for version, item in VERSIONS.iteritems():
    item.name = 'python'
    item.version = version
