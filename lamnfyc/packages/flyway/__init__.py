import os
import collections
import distutils
import distutils.dir_util

import lamnfyc.decorators
import lamnfyc.context_managers
import lamnfyc.settings
import lamnfyc.packages.base


@lamnfyc.decorators.check_installed('bin/flyway')
def installer(package, temp, env):
    with lamnfyc.context_managers.chdir(os.path.join(temp)):
        distutils.dir_util.copy_tree('flyway-{}'.format(package.version),
                                     os.path.join(lamnfyc.settings.environment_path,
                                                  'etc/flyway-{}'.format(package.version)))

        os.symlink(os.path.join(lamnfyc.settings.environment_path, 'etc/flyway-{}/flyway'.format(package.version)),
                   os.path.join(lamnfyc.settings.environment_path, 'bin/flyway'))


VERSIONS = collections.OrderedDict()
VERSIONS['4.1.1'] = lamnfyc.packages.base.TarPacket('https://search.maven.org/remotecontent?filepath=org/flywaydb/flyway-commandline/4.1.1/flyway-commandline-4.1.1.tar.gz',  # noqa
                                                     cache_key='flyway-commandline-4.1.1.tar.gz',
                                                     installer=installer,
                                                     sha256_signature='7df1f469e2efb5619a461e287dfc123b7a02389a21cbae944fd5d06bf028c287',  # noqa
                                                     depends_on=[
                                                         lamnfyc.packages.base.RequiredPacket(name='java', version='8u121'),  # noqa
                                                     ])

for version, item in VERSIONS.iteritems():
    item.name = 'flyway'
    item.version = version
