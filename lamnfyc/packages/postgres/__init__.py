import os
import collections
import subprocess

import lamnfyc.context_managers
import lamnfyc.settings
import lamnfyc.decorators
import lamnfyc.packages.base


@lamnfyc.decorators.check_installed('bin/postgres')
def installer(package, temp, env):
    command = '''LDFLAGS="-L{path}/lib"
                 LD_LIBRARY_PATH={path}/lib
                 CPPFLAGS="-I{path}/include -I{path}/ssl" ./configure --prefix={path}'''
    with lamnfyc.context_managers.chdir(os.path.join(temp, 'postgresql-{}'.format(package.version))):
        subprocess.call(command.format(path=lamnfyc.settings.environment_path), shell=True)
        subprocess.call('make && make install-world-contrib-recurse', shell=True)

        # Install all the contrib files
        subprocess.call('cd contrib/adminpack; make install', shell=True)
        subprocess.call('cd contrib/dblink; make install', shell=True)
        subprocess.call('cd contrib/fuzzystrmatch; make install', shell=True)
        subprocess.call('cd contrib/lo; make install', shell=True)
        subprocess.call('cd contrib/uuid-ossp; make install', shell=True)
        subprocess.call('cd contrib/pg_buffercache; make install', shell=True)
        subprocess.call('cd contrib/pg_trgm; make install', shell=True)
        subprocess.call('cd contrib/pgcrypto; make install', shell=True)
        subprocess.call('cd contrib/tsearch2; make install', shell=True)
        subprocess.call('cd contrib/vacuumlo; make install', shell=True)
        subprocess.call('cd contrib/xml2; make install', shell=True)
        subprocess.call('cd contrib/intarray; make install', shell=True)
        subprocess.call('cd contrib/pg_upgrade; make install', shell=True)
        subprocess.call('cd contrib/pg_upgrade_support; make install', shell=True)
        subprocess.call('cd contrib/hstore; make install', shell=True)


class PostgresPackage(lamnfyc.packages.base.TarPacket):
    BASE_PATH = os.path.dirname(os.path.realpath(__file__))

    # attributed to the environment if not there
    ENVIRONMENT_VARIABLES = (
        # if the user is using unix_sockets it will use the $VIRTUAL_ENV/run otherwise it will use 127.0.0.1
        ('PGHOST', lamnfyc.packages.base.change_to_if('127.0.0.1', '$VIRTUAL_ENV/run',
                                                      lambda options: options.unix_sockets)),
        # only display the port if the user is not using sockets
        lamnfyc.packages.base.required_if(('PGPORT', '$(random_port)',), lambda options: not options.unix_sockets),
        ('PGUSER', '$USER',),
        ('POSTGRES_PID', '$VIRTUAL_ENV/data/postmaster.pid',),
        ('PGDATABASE', 'postgres',),
    )

    def __init__(self, *args, **kwargs):
        super(PostgresPackage, self).__init__(*args, **kwargs)

        self.options.unix_sockets = False
        self.options.max_files_per_process = 100
        self.options.max_connections = 120

    def init_options(self, options):
        self.options.unix_sockets = options.pop('unix_sockets', self.options.unix_sockets)
        self.options.max_files_per_process = options.pop('max_files_per_process', self.options.max_files_per_process)
        self.options.max_connections = options.pop('max_connections', self.options.max_connections)


VERSIONS = collections.OrderedDict()
VERSIONS['9.3.9'] = PostgresPackage('https://ftp.postgresql.org/pub/source/v9.3.9/postgresql-9.3.9.tar.bz2',
                                    installer=installer, sha256_signature='f73bd0ec2028511732430beb22414a022d2114231366e8cbe78c149793910549',  # noqa
                                    depends_on=[
                                        lamnfyc.packages.base.RequiredPacket(name='readline', version='6.3'),
                                        lamnfyc.packages.base.RequiredPacket(name='openssl', version='1.0.2g'),
                                    ])

VERSIONS['9.5.4'] = PostgresPackage('https://ftp.postgresql.org/pub/source/v9.5.4/postgresql-9.5.4.tar.bz2',
                                    installer=installer, sha256_signature='cf5e571164ad66028ecd7dd8819e3765470d45bcd440d258b686be7e69c76ed0',  # noqa
                                    depends_on=[
                                        lamnfyc.packages.base.RequiredPacket(name='readline', version='6.3'),
                                        lamnfyc.packages.base.RequiredPacket(name='openssl', version='1.0.2g'),
                                    ])

for version, item in VERSIONS.iteritems():
    item.name = 'postgres'
    item.version = version
