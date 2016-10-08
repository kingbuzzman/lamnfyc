import importlib
import contextlib
import urllib2
import subprocess
import StringIO

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


def syscall(command, **kwargs):
    stdout = StringIO.StringIO()
    stderr = StringIO.StringIO()
    acceptable_codes = tuple(kwargs.pop('acceptable_codes', (0,)))
    kwargs['shell'] = kwargs.get('shell', True)
    kwargs['stdout'] = kwargs.get('stdout', subprocess.PIPE)
    kwargs['stderr'] = kwargs.get('stderr', subprocess.PIPE)

    log.debug('$ ' + command)
    proc = subprocess.Popen(command, **kwargs)
    while True:
        _stdout = proc.stdout.readline().replace('\n', '')
        _stderr = proc.stderr.readline().replace('\n', '')

        if _stdout:
            log.debug(_stdout)
            stdout.writelines([_stdout])

        if _stderr:
            # There are is a lot of output that gets thrown to stderr that is
            # more of a warning than error, and this will just scare the users
            # more than be informative
            log.debug(_stderr)
            stdout.writelines([_stderr])

        if not _stdout and not _stderr:
            break

    code = proc.wait()
    if code not in acceptable_codes:
        raise Exception('Command {} generated a {} code, acceptable codes are: {}'.format(command, code,
                                                                                          acceptable_codes))
    stdout.seek(0)
    stderr.seek(0)
    return stdout, stderr, code


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
