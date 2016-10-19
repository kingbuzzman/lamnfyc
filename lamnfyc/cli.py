import os
import jinja2
import sys
import argparse
import pkg_resources
import concurrent.futures
import operator
import re
import shutil
import collections
import stat

import lamnfyc.settings
import lamnfyc.utils
from lamnfyc.logger import (log, start_file_log)

__version__ = pkg_resources.get_distribution('lamnfyc').version


class ArgumentParser(argparse.ArgumentParser):
    def parse_known_args(self, *_args, **kwargs):
        args, namespace = super(ArgumentParser, self).parse_known_args(*_args, **kwargs)

        if args.init:
            if os.path.exists(self.config_default):
                raise self.error('File {} already exists.'.format(self.config_default))
            shutil.copyfile(os.path.join(lamnfyc.settings.BASE_PATH, self.default_name), self.config_default)
            sys.exit(0)
        elif not args.environment:
            self.error("the environment name is required")

        if not os.path.exists(args.config):
            raise self.error('{} does not exist'.format(args.config))

        return args, namespace


def parser():
    parser = ArgumentParser(description='LAMNFYC. v.{}'.format(__version__))
    parser.default_name = default_name = 'lamnfyc.yaml'
    parser.config_default = config_default = os.path.join(os.getcwd(), default_name)

    parser.add_argument('-c', '--config', default=config_default,
                        help='path to the config file, [default: {}]'.format(config_default))
    parser.add_argument('environment', nargs='?', help='path to the environment')
    parser.add_argument('--init', action='store_true',
                        help='creates a {} file inside your current working directory'.format(default_name))
    parser.add_argument('--prompt-all', action='store_true', default=False,
                        help='prompt me for every option, don\'t default anything')
    parser.add_argument('--reuse', action='store_true', default=False, help=argparse.SUPPRESS)
    parser.add_argument('--version', action='version', version='%(prog)s (version {})'.format(__version__))
    parser.add_argument(
        '-v', '--verbosity', action='store', dest='verbosity', default=20,
        type=int, choices=[10, 20, 0],
        help='Verbosity level; 0=normal output, 10=DEBUG, 20=INFO',
    )

    return parser


def main():
    args, _ = parser().parse_known_args()
    return _main(args)


def _main(args):
    environment_config = lamnfyc.utils.Configuration(args.config)
    # need the absolute path to the environment
    lamnfyc.settings.environment_path = os.path.abspath(os.path.join(os.path.abspath(os.path.curdir),
                                                                     args.environment).rstrip('/'))

    # sets up the system path local to where the yaml file is so you can import the pre/post hooks
    sys.path.insert(0, os.path.dirname(os.path.abspath(args.config)))

    # set the logging level to console only
    log.handlers[0].setLevel(args.verbosity)

    # create the cache dir if its missing
    if not os.path.isdir(lamnfyc.settings.CACHE_PATH):
        os.mkdir(lamnfyc.settings.CACHE_PATH)

    if not args.reuse:
        log.debug('Starting environment: {}'.format(lamnfyc.settings.environment_path))
        # error out if the environment already exists
        if os.path.isdir(lamnfyc.settings.environment_path):
            log.fatal('ERROR: File already exists and is not a directory.')
            log.fatal('Please provide a different path or delete the directory.')
            sys.exit(3)

        # make sure all the paths exists
        os.mkdir(lamnfyc.settings.environment_path)
        # Standard unix installation structure
        os.mkdir(os.path.join(lamnfyc.settings.environment_path, 'lib'))
        os.mkdir(os.path.join(lamnfyc.settings.environment_path, 'bin'))
        os.mkdir(os.path.join(lamnfyc.settings.environment_path, 'share'))
        os.mkdir(os.path.join(lamnfyc.settings.environment_path, 'include'))
        # Appended structure, to house configuration files, logs, and sock/run files
        os.mkdir(os.path.join(lamnfyc.settings.environment_path, 'conf'))
        os.mkdir(os.path.join(lamnfyc.settings.environment_path, 'logs'))
        os.mkdir(os.path.join(lamnfyc.settings.environment_path, 'run'))
    else:
        log.warn('Reuse mode enabled, this is not fully supported')

    # initialize the file level logging
    start_file_log(lamnfyc.settings.environment_path)

    if environment_config.preinstall_hook:
        environment_config.preinstall_hook()

    environment_config.prompt_missing(missing_only=not args.prompt_all)

    kwargs = {
        'environment_path': lamnfyc.settings.environment_path,
        'enironment_variables': variable_order(environment_config.env),
        'unset_variables': ' '.join(environment_config.env.keys()),
        'environment_path': lamnfyc.settings.environment_path
    }
    path = os.path.join(lamnfyc.settings.BASE_PATH, 'templates')
    files = [os.path.join(root, file) for root, dir, files in os.walk(path) for file in files]
    for file in files:
        file_path = os.path.join(lamnfyc.settings.environment_path, file.replace(path + os.path.sep, ''))
        with open(file_path, 'w') as file_out:
            file_out.write(jinja2.Template(open(file).read()).render(**kwargs))

        # If it goes inside /bin then give it exec permissions
        if file_path.replace(lamnfyc.settings.environment_path + os.path.sep, '').split(os.path.sep)[0] == 'bin':
            os.chmod(file_path, os.stat(file).st_mode | stat.S_IEXEC)

    # after all the environment variables have been written, lets read them back up to get nice and clean values
    # without any $VARIABLE in them
    environment_config.reload_env(lamnfyc.settings.environment_path)

    # generate all the packages we need to download
    downloads = []
    for package_item in environment_config.packages:
        package = lamnfyc.utils.import_package(package_item['name'], package_item['version'])
        package.environment_vars = environment_config.env
        downloads.append(package)

        for subpackage in package.dependencies():
            downloads.append(subpackage)
            subpackage.environment_vars = environment_config.env

    # download all the packages that are missing
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        executor.map(lambda package: package.download() if not package.cache_exists else None, downloads)

    # Install all packages, uppermost first, meaning;
    # If say Package1 depends on Package2 which in turn that depends on Package3, the order or the install will be:
    # Package3 gets installed first, then Package2, and lastly Package1
    for package_item in environment_config.packages:
        package = lamnfyc.utils.import_package(package_item['name'], package_item['version'])

        for subpackage in package.dependencies():
            subpackage.expand()

        package.expand()

    if environment_config.postinstall_callback:
        environment_config.postinstall_callback()


def variable_order(items):
    FIND = re.compile('\$([\w]+)')
    ready = collections.OrderedDict()
    ready['VIRTUAL_ENV'] = None
    ready['USER'] = None
    passes = 0
    while True:
        group = {}
        passes += 1
        for key, value in items.iteritems():
            if key in ready:
                continue

            if '$' in (str(value) or ''):
                groups = FIND.findall(value)
                counter = 0
                for _key in groups:
                    if _key in ready:
                        counter += 1
                if counter == len(groups):
                    group[key] = value
            else:
                group[key] = value

        for key, value in sorted(group.items(), key=operator.itemgetter(0)):
            ready[key] = value
            yield key, value

        if len(items.keys()) == (len(ready.keys()) - 2):
            break
        elif passes > 10:
            raise Exception('Weird nesting going on, could not find dependencies for: {}'.format(
                ', '.join(set(items.keys()) - set(ready.keys()))
            ))
