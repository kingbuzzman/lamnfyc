import os
import stat
import subprocess
import distutils.dir_util
import collections

import lamnfyc.utils
import lamnfyc.context_managers
import lamnfyc.settings
import lamnfyc.decorators


@lamnfyc.decorators.check_installed('bin/postgres')
def nine_one(package, temp):
    CHANGE_DEPENDENCY_COMMAND = 'install_name_tool -change {dependency} {new_dependency} {file}'
    with lamnfyc.context_managers.chdir(os.path.join(temp, 'Postgres.app/Contents/MacOS')):
        # "distutils.dir_util.copy_tree" returns a list of all the files copied, we're saving it so we can make sure
        # that all the dependencies are mapped properly
        moved = []
        moved += distutils.dir_util.copy_tree('bin', os.path.join(lamnfyc.settings.environment_path, 'bin'))
        moved += distutils.dir_util.copy_tree('lib', os.path.join(lamnfyc.settings.environment_path, 'lib'))
        moved += distutils.dir_util.copy_tree('include', os.path.join(lamnfyc.settings.environment_path, 'include'))
        moved += distutils.dir_util.copy_tree('share', os.path.join(lamnfyc.settings.environment_path, 'share'))

        # loop over all the files copied locally and extract all those that are executable
        for exe_file in [x for x in moved if os.access(x, os.X_OK)]:
            # we're looking at the signtures of the executable, looking for anything that mentions "PostgresApp"
            process = subprocess.Popen('otool -L {}'.format(exe_file), shell=True, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            fix = []
            while process.poll() is None:
                _ = process.stdout.readline()
                if 'PostgresApp' in _:
                    # if anything matches, store it for fixing
                    fix.append(_.strip().split(' ')[0])

            # loop over all the issues and remap them to the proper signature
            for dependency in fix:
                new_dependency = os.path.join(lamnfyc.settings.environment_path,
                                              os.path.join(os.path.basename(dependency), 'lib'))
                subprocess.Popen(CHANGE_DEPENDENCY_COMMAND.format(dependency=dependency, new_dependency=new_dependency,
                                                                  file=exe_file), shell=True)


class Postgres(lamnfyc.utils.ZipPacket):
    def start(self):
        pass

    def expand(self):
        base_path = os.path.join(lamnfyc.settings.BASE_PATH, 'packages', 'postgres')
        path = os.path.join(base_path, 'bin')
        files = [os.path.join(root, file) for root, dir, files in os.walk(path) for file in files]
        for file in files:
            file_path = os.path.join(lamnfyc.settings.environment_path, file.replace(base_path + '/', ''))
            with open(file_path, 'w') as file_out:
                file_out.write(lamnfyc.utils.Template.from_file(file).safe_substitute())
            st = os.stat(file_path)
            os.chmod(file_path, st.st_mode | stat.S_IEXEC)

        path = os.path.join(base_path, 'templates')
        files = [os.path.join(root, file) for root, dir, files in os.walk(path) for file in files]
        for file in files:
            file_path = os.path.join(lamnfyc.settings.environment_path, file.replace(path + '/', ''))
            with open(file_path, 'a') as file_out:
                file_out.write(lamnfyc.utils.Template.from_file(file).safe_substitute())
            st = os.stat(file_path)
            os.chmod(file_path, st.st_mode | stat.S_IEXEC)

        super(Postgres, self).expand()


VERSIONS = collections.OrderedDict()
VERSIONS['9.1.0.0'] = Postgres('https://github.com/PostgresApp/PostgresApp/releases/download/9.1.0.0/PostgresApp-9-1-0-0.zip',  # noqa
                               installer=nine_one, md5_signature='feb8b7d5bf4030995a26609067a9756c')

for version, item in VERSIONS.iteritems():
    item.name = 'postgres'
    item.version = version
