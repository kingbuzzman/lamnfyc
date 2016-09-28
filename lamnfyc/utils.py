import os
import lzma
import tarfile
import hashlib
import tempfile
import urllib2
import logging
import lamnfyc.settings
import contextlib
import shutil
import string
# import zipfile
import subprocess
import collections
import importlib

log = logging.getLogger('lamnfyc')

RequiredPacket = collections.namedtuple('RequiredPacket', 'name version')


def import_package(name, version):
    package_import = importlib.import_module(__package__ + '.packages.' + name)
    return package_import.VERSIONS[version]


def required_parameter(obj, name, message=None):
    message = message or 'Parameter {name} is required'
    if name not in obj:
        raise AttributeError(message.format(name=name))
    else:
        return obj[name]


class Template(string.Template):
    delimiter = '{{'
    pattern = r'''
    \{\{(?:
    (?P<escaped>\{\{)|
    (?P<named>[_a-z][_a-z0-9]*)\}\}|
    (?P<braced>[_a-z][_a-z0-9]*)\}\}|
    (?P<invalid>)
    )
    '''

    @classmethod
    def from_file(cls, file_path):
        with open(file_path, 'r') as file_obj:
            return cls(file_obj.read())


class BasePacket(object):
    def __init__(self, url, **kwargs):
        self.url = url
        self.installer = required_parameter(kwargs, 'installer')
        self.check_version = kwargs.get('check_version')
        self.md5_signature = kwargs.get('md5_signature')
        self._dependencies = kwargs.get('depends_on', [])
        self.path = os.path.join(lamnfyc.settings.CACHE_PATH, self.cache_key)

        # self aware variables; these get set later
        self.name = None
        self.version = None

        # self assigned at the pakage init()
        self.preinstall_callback = None
        self.postinstall_callback = None

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
        module, func = kwargs.get('preinstall_hook', '').split(':')
        if module:
            self.preinstall_callback = getattr(__import__(module), func)

        module, func = kwargs.get('postinstall_hook', '').split(':')
        if module:
            self.postinstall_callback = getattr(__import__(module), func)

    def dependencies(self):
        for dependency in self._dependencies:
            package = import_package(dependency.name, dependency.version)
            for subdependency in package.dependencies():
                yield package
            yield package

    # def install(self):
    #     if not self.cache_exists:
    #         yield self.download()

    def valid_signature(self):
        if self.md5_signature:
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
            log.warn('{}-{} hash bad. {} vs {}'.format(self.name, self.version, generated_hash, known_signature))
        return signatures_matched

    def download(self):
        log.debug('Downloading {}-{}, saving it to {}'.format(self.name, self.version, self.path))
        # make a request to the url, open the file we need to save it to
        with contextlib.closing(urllib2.urlopen(self.url)) as response, open(self.path, 'wb') as fileout:
            # endless loop to read 16 * 1024 bytes in at a time until its done
            while True:
                chunk = response.read(16 * 1024)
                if not chunk:
                    break
                # write what we go back
                fileout.write(chunk)
        log.debug('Download {}-{} complete'.format(self.name, self.version))
        return True

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

        log.info('Extracting {}-{}'.format(self.name, self.version))
        with self.tempdir() as temp, tarfile_obj as tar_file:
            tar_file.extractall(temp)

            self.installer(self, temp)

        if self.postinstall_callback:
            self.postinstall_callback()


class ZipPacket(BasePacket):
    def expand(self):
        if self.is_properly_installed:
            return

        if self.preinstall_callback:
            self.preinstall_callback()

        log.info('Extracting {}-{}'.format(self.name, self.version))
        with self.tempdir() as temp, open(os.devnull, 'w') as FNULL:  # , zipfile.ZipFile(self.path) as zip_file:
            # zip_file.extractall(temp)
            # Python's zip file utility has been broken since 2012 im forced to come up with this work around because
            # i absolutely need to maintain the file permisions; ie. executable/read
            subprocess.call('unzip {source} -d {destination}'.format(source=self.path, destination=temp),
                            shell=True, stdout=FNULL, stderr=FNULL)
            self.installer(self, temp)

        if self.postinstall_callback:
            self.postinstall_callback()
