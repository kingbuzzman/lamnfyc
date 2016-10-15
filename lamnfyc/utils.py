import yaml
import importlib
import contextlib
import urllib2
import subprocess
import os
import operator

from lamnfyc.logger import log  # noqa


def import_package(name, version):
    package_import = importlib.import_module(__package__ + '.packages.' + name)
    try:
        return package_import.VERSIONS[version]
    except KeyError:
        raise KeyError('{} {} was not found, these are the options: {}'.format(
            name, version, ', '.join(package_import.VERSIONS)
        ))


def import_function(function_name):
    module, _, func = (function_name or '').partition(':')
    if module:
        try:
            return getattr(__import__(module), func)
        except AttributeError:
            raise ImportError('Could not import {}'.format(function_name))
    return None


def required_parameter(obj, name, message=None):
    message = message or 'Parameter {name} is required'
    if name not in obj:
        raise AttributeError(message.format(name=name))
    else:
        return obj[name]


def download(url, path, chunk_size=16 * 1024):
    with contextlib.closing(urllib2.urlopen(url)) as response, open(path, 'wb') as fileout:
        # endless loop to read `chunk_size` bytes in at a time until its done
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            # write what we go back
            fileout.write(chunk)


class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


class Configuration(object):

    MESSAGE = 'What is the value for {name}? [defaults: "{default}"] '

    def __init__(self, file_path):
        _config = yaml.load(open(file_path).read())
        _config['environment'] = _config.get('environment') or {}
        _config['environment']['inherits'] = _config['environment'].get('inherits') or None
        # _config['environment']['message'] = _config['environment'].get('message') or self.MESSAGE
        _config['environment']['defaults'] = _config['environment'].get('defaults') or {}
        _config['environment']['required'] = _config['environment'].get('required') or []

        self.MESSAGE = 'What is the value for {name}? [defaults: "{default}"] '
        self.MESSAGE = _config['environment'].get('message') or self.MESSAGE

        self.preinstall_hook = import_function(_config.get('packages_preinstall_hook'))
        self.postinstall_callback = import_function(_config.get('packages_postinstall_hook'))

        self.packages = _config.get('packages') or []
        self.env = {}
        if _config['environment']['inherits']:
            abs_path = os.path.join(os.path.dirname(os.path.abspath(file_path)), _config['environment']['inherits'])
            self.env = self.load_env_extend(abs_path)
        self.env.update(_config['environment']['defaults'])
        self.env.update({key: None for key in _config['environment']['required']})

        for package_item in self.packages:
            package = import_package(package_item['name'], package_item['version'])
            package.init(**package_item)

            for key, value in package.environment_variables:
                if key not in self.env:
                    self.env[key] = value

    @classmethod
    def load_env_extend(cls, file_path):
        _config = yaml.load(open(file_path).read())
        _config['environment']['inherits'] = _config['environment'].get('inherits') or None
        # _config['environment']['message'] = _config['environment'].get('message') or cls.MESSAGE
        _config['environment']['defaults'] = _config['environment'].get('defaults') or {}
        _config['environment']['required'] = _config['environment'].get('required') or []

        env = {}
        if _config['environment']['inherits']:
            abs_path = os.path.join(os.path.dirname(os.path.abspath(file_path)), _config['environment']['inherits'])
            env = cls.load_env_extend(abs_path)
        env.update(_config['environment']['defaults'])
        env.update({key: None for key in _config['environment']['required']})

        return env

    def prompt_missing(self, missing_only=True):
        MESSAGE = self.MESSAGE
        for variable, value in sorted(self.env.items(), key=operator.itemgetter(0)):
            if not missing_only or value is None or value == '':
                message = MESSAGE.format(name=variable, default=value or '')
                value = raw_input(message) or value or ''
            else:
                value = value or ''
            self.env[variable] = value

    def reload_env(self, environment_path):
        command = 'bash -c "export VIRTUAL_ENV={0}; export PATH={0}/bin:$PATH; source {0}/environment; env"'
        proc = subprocess.Popen(command.format(environment_path), shell=True, stdout=subprocess.PIPE)
        self.env = dict((line.split("=", 1) for line in proc.stdout.read().splitlines()))
