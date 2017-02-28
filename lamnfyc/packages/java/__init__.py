import os
import collections
import distutils
import functools
import urllib2
import contextlib
import distutils.dir_util

import lamnfyc.context_managers
import lamnfyc.settings
import lamnfyc.packages.base


def installer_8u121(package, temp, env):
    with lamnfyc.context_managers.chdir(os.path.join(temp, 'jre1.8.0_121.jre', 'Contents', 'Home')):
        distutils.dir_util.copy_tree('bin', os.path.join(lamnfyc.settings.environment_path, 'bin'))
        distutils.dir_util.copy_tree('lib', os.path.join(lamnfyc.settings.environment_path, 'lib'))
        distutils.dir_util.copy_tree('man', os.path.join(lamnfyc.settings.environment_path, 'man'))


def generate_auth(url):
    """
    By installing java you've accepted the terms and conditions
    """
    headers = {
        'upgrade-insecure-requests': '1',
        'cache-control': 'no-cache',
        'authority': 'edelivery.oracle.com',
        'cookie': 'oraclelicense=accept-securebackup-cookie;'
    }
    request = urllib2.Request(url, headers=headers)
    with contextlib.closing(urllib2.urlopen(request)) as response:
        return response.url

VERSIONS = collections.OrderedDict()
VERSIONS['8u121'] = lamnfyc.packages.base.TarPacket(functools.partial(generate_auth, 'https://edelivery.oracle.com/otn-pub/java/jdk/8u121-b13/e9e7ea248e2c4826b92b3f075a80e441/jre-8u121-macosx-x64.tar.gz'),  # noqa
                                                     installer=installer_8u121,
                                                     sha256_signature='7549541f7843be5cd507bcd91c7195c5dbbe3d222d2b322568e198f2733ba4f0')  # noqa

for version, item in VERSIONS.iteritems():
    item.name = 'java'
    item.version = version
