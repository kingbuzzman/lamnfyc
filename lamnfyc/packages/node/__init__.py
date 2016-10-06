import os
import distutils.dir_util
import collections

import lamnfyc.context_managers
import lamnfyc.settings
import lamnfyc.decorators
import lamnfyc.packages.base

from lamnfyc.logger import log


@lamnfyc.decorators.check_installed('bin/node')
def six_x_installer(package, temp):
    with lamnfyc.context_managers.chdir(os.path.join(temp, 'node-v{}-darwin-x64'.format(package.version))):
        distutils.dir_util.copy_tree('bin', os.path.join(lamnfyc.settings.environment_path, 'bin'))
        distutils.dir_util.copy_tree('lib', os.path.join(lamnfyc.settings.environment_path, 'lib'))
        distutils.dir_util.copy_tree('include', os.path.join(lamnfyc.settings.environment_path, 'include'))
        distutils.dir_util.copy_tree('share', os.path.join(lamnfyc.settings.environment_path, 'share'))
        # fixes npm link
        os.remove(os.path.join(lamnfyc.settings.environment_path, 'bin/npm'))
        os.symlink(os.path.join(lamnfyc.settings.environment_path, 'lib/node_modules/npm/bin/npm-cli.js'),
                   os.path.join(lamnfyc.settings.environment_path, 'bin/npm'))


def check_version(package, installed_version):
    installed_version = installed_version.replace('v', '')
    if installed_version == package.version:
        return True

    log.debug('{} already exists, but version {} did not match {}'.format(package.installer.path, installed_version,
                                                                          package.version))
    return False


VERSIONS = collections.OrderedDict()
VERSIONS['6.5.0'] = lamnfyc.packages.base.TarPacket('https://nodejs.org/dist/v6.5.0/node-v6.5.0-darwin-x64.tar.gz',
                                                    installer=six_x_installer, check_version=check_version,
                                                    md5_signature='44080b266b0312ed1ebe054538be520a')

VERSIONS['6.2.2'] = lamnfyc.packages.base.TarPacket('https://nodejs.org/dist/v6.2.2/node-v6.2.2-darwin-x64.tar.gz',
                                                    installer=six_x_installer, check_version=check_version,
                                                    md5_signature='6d2ea41938c4ccee53bde9423b1991fc')

for version, item in VERSIONS.iteritems():
    item.name = 'node'
    item.version = version
