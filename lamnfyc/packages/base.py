import os
import copy
import lzma
import tarfile
import hashlib
import tempfile
import contextlib
import shutil
import jinja2
import stat
# import zipfile
import subprocess
import collections

import lamnfyc.utils
import lamnfyc.settings
from lamnfyc.logger import log

RequiredPacket = collections.namedtuple('RequiredPacket', 'name version')


def required_if(environment_variable, condition):
    def wrapped(options):
        if condition(options):
            return environment_variable
    return wrapped


def change_to_if(value_to_change, default_value, condition):
    def wrapped(options):
        if condition(options):
            return default_value
        else:
            return value_to_change
    return wrapped


class BasePacket(object):
    def __init__(self, url, **kwargs):
        self.url = url
        self.installer = lamnfyc.utils.required_parameter(kwargs, 'installer')
        self.check_version = kwargs.get('check_version')
        self.md5_signature = kwargs.get('md5_signature')
        self.sha256_signature = kwargs.get('sha256_signature')
        self._dependencies = kwargs.get('depends_on', [])
        self.path = os.path.join(lamnfyc.settings.CACHE_PATH, self.cache_key)

        # self aware variables; these get set later
        self.name = None
        self.version = None

        # self assigned at the pakage init()
        self.environment_vars = None
        self.preinstall_callback = None
        self.postinstall_callback = None
        self.options = lamnfyc.utils.AttributeDict()

    @property
    def cache_key(self):
        return os.path.basename(self.url)

    @property
    def cache_exists(self):
        if os.path.exists(self.path):
            if self.valid_signature():
                return True
            log.debug('Removing the {}-{} cache file, signature was no good: {}'.format(self.name,
                                                                                        self.version,
                                                                                        self.path))
            os.remove(self.path)
        # nothing found
        return False

    @property
    def is_properly_installed(self):
        if not hasattr(self.installer, 'path'):
            return False

        relative_path = self.installer.path
        absolute_path = os.path.join(lamnfyc.settings.environment_path, relative_path)

        if os.path.isfile(absolute_path):
            if not self.check_version:
                return True

            proc = subprocess.Popen('{} --version'.format(absolute_path).split(' '), stdout=subprocess.PIPE)
            raw_version = proc.stdout.read().rstrip()
            if self.check_version(self, raw_version):
                # log.debug('{} already exists, skippping'.format(relative_path))
                return True
        return False

    def init(self, **kwargs):
        # setup the hooks for the package
        self.preinstall_callback = lamnfyc.utils.import_function(kwargs.get('preinstall_hook'))
        self.postinstall_callback = lamnfyc.utils.import_function(kwargs.get('postinstall_hook'))

        # setup the user options for the package
        options = copy.copy(kwargs.get('options', {}))
        self.init_options(options)

        # alert the user of options set that were not used by the package
        message = 'Option "{option}" was passed to the {name} package and was never used, please check the options'
        for option in options.iterkeys():
            log.warn(message.format(option=option, name=self.name))

    def init_options(self, options):
        # To be implemented by the subclass
        # Please pop the keys out of the options variable when processing them otherwise a warning will be thrown
        # example:
        # # self.option1 = options.pop('option1', True)
        # # self.option2 = options.pop('option2') # this is now required
        pass

    def dependencies(self):
        for dependency in self._dependencies:
            package = lamnfyc.utils.import_package(dependency.name, dependency.version)
            for subdependency in package.dependencies():
                yield package
            yield package

    # def install(self):
    #     if not self.cache_exists:
    #         yield self.download()

    def valid_signature(self):
        if self.sha256_signature:
            # if there is an sha256 signature to compare it to, do it!
            known_signature = self.sha256_signature
            hash_module = hashlib.sha256()
        elif self.md5_signature:
            # if there is an md5 signature to compare it to, do it!
            known_signature = self.md5_signature
            hash_module = hashlib.md5()
        else:
            log.debug('{}-{} did not have and signatures to compare'.format(self.name, self.version))
            return True

        with open(self.path, "rb") as f:
            for chunk in iter(lambda: f.read(16 * 1024), b""):
                hash_module.update(chunk)

        # check that the signatures match
        generated_hash = hash_module.hexdigest()
        signatures_matched = generated_hash == known_signature
        if signatures_matched:
            log.debug('{}-{} hash good'.format(self.name, self.version))
        else:
            log.warn('{}-{} hash bad. Received: {}, but is expected: {}'.format(self.name, self.version,
                                                                                generated_hash, known_signature))
        return signatures_matched

    def download(self):
        log.debug('Downloading {}-{}, saving it to {}'.format(self.name, self.version, self.path))
        lamnfyc.utils.download(self.url, self.path)
        log.debug('Download {}-{} complete'.format(self.name, self.version))
        return True

    @property
    def environment_variables(self):
        # loop over all the environment variables that are being attributed to the environment
        for item in getattr(self, 'ENVIRONMENT_VARIABLES', []):
            if hasattr(item, '__call__'):
                variable = item(self.options)
                # if its visible return it
                if variable:
                    yield variable
            # this is a required variable that has no default value
            elif isinstance(item, basestring):
                yield (item, None,)
            else:
                key, value = item
                if hasattr(value, '__call__'):
                    value = value(self.options)
                yield (key, value,)

    def install_templates(self):
        if not hasattr(self, 'BASE_PATH'):
            return

        template_context = {
            'environment_path': lamnfyc.settings.environment_path,
            'options': self.options
        }

        path = os.path.join(self.BASE_PATH, 'templates')
        # find all the files inside <package>/templates/
        files = [os.path.join(root, file) for root, dir, files in os.walk(path) for file in files]
        for file in files:
            # find the name of the directory that comes right after <package>/templates/
            root_dir = file.replace(path + os.path.sep, '').split(os.path.sep)[0]
            if root_dir == '__append':
                # make an absolute path to the environment excluding the */__append/*
                file_path = os.path.join(lamnfyc.settings.environment_path,
                                         file.replace(os.path.join(path, root_dir) + os.path.sep, ''))
                # we're appending
                file_obj = open(file_path, 'a')
            else:
                # make an absolute path out of the file name pointing to the environment
                file_path = os.path.join(lamnfyc.settings.environment_path, file.replace(path + os.path.sep, ''))
                # set to write
                file_obj = open(file_path, 'w')

            with file_obj as file_out:
                # TODO: is there a better way od doinf this?!
                file_out.write(jinja2.Template(open(file).read()).render(**template_context))

            # If it goes inside /bin then give it exec permissions
            if file_path.replace(lamnfyc.settings.environment_path + os.path.sep, '').split(os.path.sep)[0] == 'bin':
                os.chmod(file_path, os.stat(file).st_mode | stat.S_IEXEC)

    @contextlib.contextmanager
    def tempdir(self):
        temp_dir = tempfile.mkdtemp()
        log.debug('New temp dir for {}-{} made: {}'.format(self.name, self.version, temp_dir))
        try:
            yield temp_dir
        finally:
            shutil.rmtree(temp_dir)
            log.debug('Temp dir for {}-{} deleted: {}'.format(self.name, self.version, temp_dir))

    def expand(self):
        raise NotImplemented('This is to be implemented on the subclasses')

    def __unicode__(self):
        return u"<{}: {}-{}>".format(self.__class__.__name__, self.name, self.version)

    def __str__(self):
        return str(self.__unicode__())

    def __repr__(self):
        return str(self)


class TarPacket(BasePacket):
    def expand(self):
        if self.is_properly_installed:
            log.debug('{}-{} already installed'.format(self.name, self.version))
            return

        if self.preinstall_callback:
            self.preinstall_callback()

        if self.path.endswith('tar.xz'):
            @contextlib.contextmanager
            def xz_tar(path):
                """
                Ensures all all the files are going to get closed properly
                """
                with contextlib.closing(lzma.LZMAFile(path)) as xz:
                    yield tarfile.open(fileobj=xz)

            tarfile_obj = xz_tar(self.path)
        else:
            tarfile_obj = tarfile.open(self.path, 'r:*')

        self.install_templates()

        log.info('Extracting {}-{}'.format(self.name, self.version))
        with self.tempdir() as temp, tarfile_obj as tar_file:
            tar_file.extractall(temp)

            self.installer(self, temp, self.environment_vars)

        if self.postinstall_callback:
            self.postinstall_callback()


class ZipPacket(BasePacket):
    def expand(self):
        if self.is_properly_installed:
            log.debug('{}-{} already installed'.format(self.name, self.version))
            return

        if self.preinstall_callback:
            self.preinstall_callback()

        self.install_templates()

        log.info('Extracting {}-{}'.format(self.name, self.version))
        with self.tempdir() as temp, open(os.devnull, 'w') as FNULL:  # , zipfile.ZipFile(self.path) as zip_file:
            # zip_file.extractall(temp)
            # Python's zip file utility has been broken since 2012 im forced to come up with this work around because
            # i absolutely need to maintain the file permisions; ie. executable/read
            subprocess.call('unzip {source} -d {destination}'.format(source=self.path, destination=temp),
                            shell=True, stdout=FNULL, stderr=FNULL)
            self.installer(self, temp, self.environment_vars)

        if self.postinstall_callback:
            self.postinstall_callback()
