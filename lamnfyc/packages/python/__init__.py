import os
import subprocess
import collections

import lamnfyc.context_managers
import lamnfyc.settings
import lamnfyc.decorators
import lamnfyc.packages.base


@lamnfyc.decorators.check_installed('bin/python')
def two_seven_installer(package, temp):
    command = '''LDFLAGS="-L{path}/lib"
                 LD_LIBRARY_PATH={path}/lib
                 CPPFLAGS="-I{path}/include -I{path}/ssl" ./configure --prefix={path} --with-ensurepip=yes'''
    with lamnfyc.context_managers.chdir(os.path.join(temp, 'Python-{}'.format(package.version))):
        subprocess.call(command.format(path=lamnfyc.settings.environment_path), shell=True)
        subprocess.call('make', shell=True)
        subprocess.call('make install', shell=True)

    # upgrade pip to latests
    with lamnfyc.context_managers.chdir(os.path.join(lamnfyc.settings.environment_path, 'bin')):
        subprocess.call('pip install -U pip', shell=True)


def three_five_installer():
    raise NotImplemented()


class PythonPackage(lamnfyc.packages.base.TarPacket):
    BASE_PATH = os.path.dirname(os.path.realpath(__file__))


VERSIONS = collections.OrderedDict()
VERSIONS['3.5.0'] = PythonPackage('https://www.python.org/ftp/python/3.5.0/Python-3.5.0.tar.xz',
                                  installer=three_five_installer,
                                  md5_signature='d149d2812f10cbe04c042232e7964171',
                                  depends_on=[
                                      lamnfyc.packages.base.RequiredPacket(name='readline', version='6.3'),
                                      lamnfyc.packages.base.RequiredPacket(name='openssl', version='1.0.2g'),
                                  ])

VERSIONS['2.7.12'] = PythonPackage('https://www.python.org/ftp/python/2.7.12/Python-2.7.12.tar.xz',
                                   installer=two_seven_installer,
                                   md5_signature='57dffcee9cee8bb2ab5f82af1d8e9a69',
                                   depends_on=[
                                       lamnfyc.packages.base.RequiredPacket(name='readline', version='6.3'),
                                       lamnfyc.packages.base.RequiredPacket(name='openssl', version='1.0.2g'),
                                   ])

VERSIONS['2.7.9'] = PythonPackage('https://www.python.org/ftp/python/2.7.9/Python-2.7.9.tar.xz',
                                  installer=two_seven_installer,
                                  md5_signature='38d530f7efc373d64a8fb1637e3baaa7',
                                  depends_on=[
                                      lamnfyc.packages.base.RequiredPacket(name='readline', version='6.3'),
                                      lamnfyc.packages.base.RequiredPacket(name='openssl', version='1.0.2g'),
                                  ])

VERSIONS['2.7.6'] = PythonPackage('https://www.python.org/ftp/python/2.7.6/Python-2.7.6.tar.xz',
                                  installer=two_seven_installer,
                                  md5_signature='bcf93efa8eaf383c98ed3ce40b763497',
                                  depends_on=[
                                      lamnfyc.packages.base.RequiredPacket(name='readline', version='6.3'),
                                      lamnfyc.packages.base.RequiredPacket(name='openssl', version='1.0.2g'),
                                  ])

for version, item in VERSIONS.iteritems():
    item.name = 'python'
    item.version = version
