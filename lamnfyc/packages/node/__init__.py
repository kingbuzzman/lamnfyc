import os
import distutils.dir_util
import collections

import lamnfyc.utils
import lamnfyc.context_managers
import lamnfyc.settings
import lamnfyc.decorators


@lamnfyc.decorators.check_installed('bin/node')
def six_two_installer(package, temp):
    with lamnfyc.context_managers.chdir(os.path.join(temp, 'node-v{}-darwin-x64'.format(package.version))):
        distutils.dir_util.copy_tree('bin', os.path.join(lamnfyc.settings.environment_path, 'bin'))
        distutils.dir_util.copy_tree('lib', os.path.join(lamnfyc.settings.environment_path, 'lib'))
        distutils.dir_util.copy_tree('include', os.path.join(lamnfyc.settings.environment_path, 'include'))
        distutils.dir_util.copy_tree('share', os.path.join(lamnfyc.settings.environment_path, 'share'))
        # fixes npm link
        os.remove(os.path.join(lamnfyc.settings.environment_path, 'bin/npm'))
        os.symlink(os.path.join(lamnfyc.settings.environment_path, 'lib/node_modules/npm/bin/npm-cli.js'),
                   os.path.join(lamnfyc.settings.environment_path, 'bin/npm'))


VERSIONS = collections.OrderedDict()
VERSIONS['6.2.2'] = lamnfyc.utils.TarPacket('https://nodejs.org/dist/v6.2.2/node-v6.2.2-darwin-x64.tar.gz',
                                            installer=six_two_installer,
                                            md5_signature='6d2ea41938c4ccee53bde9423b1991fc')

for version, item in VERSIONS.iteritems():
    item.name = 'node'
    item.version = version
