import os
import jinja2
import sys
import yaml
import argparse
import pkg_resources
import concurrent.futures
import copy
import operator
import re
import collections
import stat

import lamnfyc.settings
import lamnfyc.utils
from lamnfyc.logger import log

__version__ = pkg_resources.get_distribution('lamnfyc').version


def main():
    parser = argparse.ArgumentParser(description='LAMNFYC. v.{}'.format(__version__))
    config_default = os.path.join(os.getcwd(), 'lamnfyc.yaml')
    # sets up the system path local to where the yaml file is so you can import the pre/post hooks
    sys.path.insert(0, os.path.split(config_default)[0])

    parser.add_argument('-c', '--config', default=config_default,
                        help='path to the config file, [default: {}]'.format(config_default))
    parser.add_argument('environment', help='path to the environment')
    parser.add_argument('--reuse', action='store_true', default=False, help=argparse.SUPPRESS)
    parser.add_argument('--version', action='version', version='%(prog)s (version {})'.format(__version__))
    parser.add_argument(
        '-v', '--verbosity', action='store', dest='verbosity', default=20,
        type=int, choices=[10, 20, 0],
        help='Verbosity level; 0=normal output, 10=DEBUG, 20=INFO',
    )

    args, vargs = parser.parse_known_args()
    environment_config = yaml.load(open(args.config).read())
    lamnfyc.settings.environment_path = os.path.join(os.path.abspath(os.path.curdir), args.environment).rstrip('/')

    # set the logging level
    log.setLevel(args.verbosity)

    # create the cache dir if its missing
    if not os.path.isdir(lamnfyc.settings.CACHE_PATH):
        os.mkdir(lamnfyc.settings.CACHE_PATH)

    if not args.reuse:
        # error out if the environment already exists
        if os.path.isdir(args.environment):
            log.fatal('ERROR: File already exists and is not a directory.')
            log.fatal('Please provide a different path or delete the directory.')
            sys.exit(3)

        # make sure all the paths exists
        os.mkdir(args.environment)
        os.mkdir(os.path.join(args.environment, 'lib'))
        os.mkdir(os.path.join(args.environment, 'bin'))
        os.mkdir(os.path.join(args.environment, 'share'))
        os.mkdir(os.path.join(args.environment, 'include'))
        os.mkdir(os.path.join(args.environment, 'logs'))
        os.mkdir(os.path.join(args.environment, 'run'))
    else:
        log.warn('Reuse mode enabled, this is not fully supported')

    preinstall_hook = lamnfyc.utils.import_function(environment_config.get('packages_preinstall_hook'))
    postinstall_callback = lamnfyc.utils.import_function(environment_config.get('packages_postinstall_hook'))

    if preinstall_hook:
        preinstall_hook()

    env = copy.copy(environment_config.get('environment', {}).get('defaults', {}))
    env.update({key: None for key in environment_config.get('environment', {}).get('required', {}) or {}})

    for package_item in environment_config['packages']:
        package = lamnfyc.utils.import_package(package_item['name'], package_item['version'])
        package.init(**package_item)
        for key, value in package.environment_variables:
            if key not in env:
                env[key] = value

    MESSAGE = 'What is the value for {name}? [defaults: "{default}"] '
    MESSAGE = environment_config.get('environment', {}).get('message', MESSAGE)

    print 'Please enter or confirm the following environment variables, remember: When in doubt, leave-the-default'
    for variable, value in sorted(env.items(), key=operator.itemgetter(0)):
        message = MESSAGE.format(name=variable, default=value or '')
        env[variable] = raw_input(message) or value or None

    kwargs = {
        'environment_path': lamnfyc.settings.environment_path,
        'enironment_variables': variable_order(env),
        'unset_variables': ' '.join(env.keys()),
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

    # generate all the packages we need to download
    downloads = []
    for package_item in environment_config['packages']:
        package = lamnfyc.utils.import_package(package_item['name'], package_item['version'])
        downloads.append(package)

        for subpackage in package.dependencies():
            downloads.append(subpackage)

    # download all the packages that are missing
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        executor.map(lambda package: package.download() if not package.cache_exists else None, downloads)

    # Install all packages, uppermost first, meaning;
    # If say Package1 depends on Package2 which in turn that depends on Package3, the order or the install will be:
    # Package3 gets installed first, then Package2, and lastly Package1
    for package_item in environment_config['packages']:
        package = lamnfyc.utils.import_package(package_item['name'], package_item['version'])

        for subpackage in package.dependencies():
            subpackage.expand()

        package.expand()

    if postinstall_callback:
        postinstall_callback()


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
            if key in ready or key in group:
                continue

            if '$' in (str(value) or ''):
                groups = FIND.findall(value)
                counter = 0
                for _key in groups:
                    if _key in ready or _key in group:
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
