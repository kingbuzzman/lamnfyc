import os
import collections
import subprocess

import lamnfyc.context_managers
import lamnfyc.settings
import lamnfyc.packages.base
import lamnfyc.decorators


@lamnfyc.decorators.check_installed('lib/libldap.a')
def two_four_installer(package, temp, env):
    with lamnfyc.context_managers.chdir(os.path.join(temp, 'openldap-{}'.format(package.version))):
        args = ('--enable-bdb=no '
                '--enable-hdb=no '
                '--prefix={path} '
                '--sysconfdir={path} '
                '--localstatedir={path}')
        command = '''LDFLAGS="-L{path}/lib"
                     LD_LIBRARY_PATH={path}/lib
                     CPPFLAGS="-I{path}/include -I{path}/ssl" ./configure ''' + args
        subprocess.call(command.format(path=lamnfyc.settings.environment_path), shell=True)
        subprocess.call('make && make install', shell=True)


VERSIONS = collections.OrderedDict()
VERSIONS['2.4.44'] = lamnfyc.packages.base.TarPacket('ftp://ftp.openldap.org/pub/OpenLDAP/openldap-release/openldap-2.4.44.tgz',  # noqa
                                                     installer=two_four_installer,
                                                     md5_signature='693ac26de86231f8dcae2b4e9d768e51',
                                                     depends_on=[
                                                         lamnfyc.packages.base.RequiredPacket(name='openssl', version='1.0.2g'),  # noqa
                                                         lamnfyc.packages.base.RequiredPacket(name='groff', version='1.22.3'),  # noqa
                                                     ])

for version, item in VERSIONS.iteritems():
    item.name = 'openldap'
    item.version = version
