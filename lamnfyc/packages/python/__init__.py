import os
import collections

import lamnfyc.context_managers
import lamnfyc.settings
import lamnfyc.decorators
import lamnfyc.packages.base
import subprocess


@lamnfyc.decorators.check_installed('bin/python')
def two_seven_installer(package, temp, env):
    command = '''LDFLAGS="-L{path}/lib"
                 CPPFLAGS="-I{path}/include -I{path}/ssl"
                 CFLAGS="-I{path}/include"
                 LD_LIBRARY_PATH={path}/lib ./configure --prefix={path} --enable-shared --with-ensurepip=yes'''
    temp = os.path.join(temp, 'Python-{}'.format(package.version))
    with lamnfyc.context_managers.chdir(temp):
        subprocess.call(command.format(path=lamnfyc.settings.environment_path), env=env, shell=True)
        subprocess.call('make', env=env, shell=True)
        subprocess.call('make install', env=env, shell=True)

        # pip doenst exist, need to go get it
        if not os.path.exists(os.path.join(lamnfyc.settings.environment_path, 'bin', 'pip')):
            ez_setup_path = os.path.join(temp, 'ez_setup.py')
            lamnfyc.utils.download('https://bootstrap.pypa.io/ez_setup.py', ez_setup_path)
            subprocess.call('python {}'.format(ez_setup_path), env=env, shell=True)
            subprocess.call('easy_install pip', env=env, shell=True)

    # upgrade pip to latests
    subprocess.call('pip install -U pip', env=env, shell=True)


def three_five_installer():
    raise NotImplemented()


class PythonPackage(lamnfyc.packages.base.TarPacket):
    BASE_PATH = os.path.dirname(os.path.realpath(__file__))


class Python27Package(PythonPackage):
    """
    Used for python < 2.7.9 where pip was not integrated
    """
    # attributed to the environment if not there
    ENVIRONMENT_VARIABLES = (
        ('PYTHONNOUSERSITE', '$VIRTUAL_ENV/lib/python2.7/site-packages',),
    )


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

VERSIONS['2.7.6'] = Python27Package('https://www.python.org/ftp/python/2.7.6/Python-2.7.6.tar.xz',
                                    installer=two_seven_installer,
                                    md5_signature='bcf93efa8eaf383c98ed3ce40b763497',
                                    depends_on=[
                                        lamnfyc.packages.base.RequiredPacket(name='readline', version='6.3'),
                                        lamnfyc.packages.base.RequiredPacket(name='openssl', version='1.0.2g'),
                                    ])

for version, item in VERSIONS.iteritems():
    item.name = 'python'
    item.version = version
