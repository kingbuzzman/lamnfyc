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


class BasePacket(object):
    def __init__(self, url, **kwargs):
        self.url = url
        self.installer = required_parameter(kwargs, 'installer')
        self.md5_signature = kwargs.get('md5_signature')
        self._dependencies = kwargs.get('depends_on', [])
        self.path = os.path.join(lamnfyc.settings.CACHE_PATH, self.cache_key)

        # self aware variables; these get set later
        self.name = None
        self.version = None

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

    def dependencies(self, depth=1):
        for dependency in self._dependencies:
            package = import_package(dependency.name, dependency.version)
            for subdependency in package.dependencies(depth + 1):
                yield package, depth + 1
            yield package, depth

    def install(self):
        if not self.cache_exists:
            yield self.download()

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
        if self.installer.installed():
            return

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


class ZipPacket(BasePacket):
    def expand(self):
        if self.installer.installed():
            return

        log.info('Extracting {}-{}'.format(self.name, self.version))
        with self.tempdir() as temp, open(os.devnull, 'w') as FNULL:  # , zipfile.ZipFile(self.path) as zip_file:
            # zip_file.extractall(temp)
            # Python's zip file utility has been broken since 2012 im forced to come up with this work around because
            # i absolutely need to maintain the file permisions; ie. executable/read
            subprocess.call('unzip {source} -d {destination}'.format(source=self.path, destination=temp),
                            shell=True, stdout=FNULL, stderr=FNULL)
            self.installer(self, temp)
