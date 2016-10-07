import importlib

from lamnfyc.logger import log  # noqa


def import_package(name, version):
    package_import = importlib.import_module(__package__ + '.packages.' + name)
    return package_import.VERSIONS[version]


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


class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


def download(url, path, chunk_size=16 * 1024):
    with contextlib.closing(urllib2.urlopen(url)) as response, open(path, 'wb') as fileout:
        # endless loop to read `chunk_size` bytes in at a time until its done
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            # write what we go back
            fileout.write(chunk)
