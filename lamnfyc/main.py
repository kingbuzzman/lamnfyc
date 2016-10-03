import os
import sys
import yaml
import argparse
import pkg_resources
import logging
import concurrent.futures
import copy
import subprocess
import stat
import operator
import re
import collections

import lamnfyc.settings
import lamnfyc.utils

__version__ = pkg_resources.get_distribution('lamnfyc').version
log = logging.getLogger('lamnfyc')
log.setLevel(logging.DEBUG)
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
log.addHandler(console)


def main():
    parser = argparse.ArgumentParser(description='LAMNFYC. v.{}'.format(__version__))
    config_default = os.path.join(os.getcwd(), 'lamnfyc.yaml')
    parser.add_argument('-c', '--config', default=config_default,
                        help='path to the config file, [default: {}]'.format(config_default))
    parser.add_argument('environment', help='path to the environment')
    parser.add_argument('--version', action='version', version='%(prog)s (version {})'.format(__version__))
    parser.add_argument('--verbose', action='store_true')

    args, vargs = parser.parse_known_args()
    environment_config = yaml.load(open(args.config).read())
    lamnfyc.settings.environment_path = os.path.join(os.path.abspath(os.path.curdir), args.environment).rstrip('/')

    # create the cache dir if its missing
    if not os.path.isdir(lamnfyc.settings.CACHE_PATH):
        os.mkdir(lamnfyc.settings.CACHE_PATH)

    if os.path.isdir(args.environment):
        log.fatal('ERROR: File already exists and is not a directory.')
        log.fatal('Please provide a different path or delete the file.')
        sys.exit(3)

    # make sure all the paths exists
    os.mkdir(args.environment)
    os.mkdir(os.path.join(args.environment, 'lib'))
    os.mkdir(os.path.join(args.environment, 'bin'))
    os.mkdir(os.path.join(args.environment, 'share'))
    os.mkdir(os.path.join(args.environment, 'include'))
    os.mkdir(os.path.join(args.environment, 'logs'))
    os.mkdir(os.path.join(args.environment, 'run'))

    # # proc = subprocess.Popen(['bash', '-c', 'eval $(cat {} | sed "s/\$/\\$/g"); env'.format(os.path.join(args.environment, 'environment'))], stdout=subprocess.PIPE)
    # # source_env = {tup[0].strip(): tup[1].strip() for tup in map(lambda s: s.strip().split('=', 1), proc.stdout)}
    # source_env = {}
    # file_name = os.path.join(args.environment, 'environment')
    # if os.path.isfile(file_name):
    #     with open(file_name, 'r') as environ:
    #         for line in environ:
    #             if not line.startswith('export '):
    #                 continue
    #             # line = line.replace('export ', '')
    #             key, value = line[7:].split('=', 1)
    #             value = value.strip()
    #             if value[0] == value[-1] and value.startswith(("'", '"')):
    #                 value = value[1:-1]
    #             source_env[key.strip()] = value

    env = copy.copy(environment_config['environment']['defaults'])
    env.update({key: None for key in environment_config['environment']['required']})

    for variable, value in sorted(env.items(), key=operator.itemgetter(0)):
        # if variable in source_env and source_env[variable]:
        #     env[variable] = source_env[variable]
        #     continue
        message = environment_config['environment']['message'].format(name=variable, default=value or '')
        env[variable] = value #raw_input(message) or value or None

    with open(os.path.join(lamnfyc.settings.environment_path, 'environment'), 'w') as f:
        f.write('# this is a generated file, do not add anything to this\n')
        f.write("""
urlencode() {
    # urlencode <string>
    old_lc_collate=$LC_COLLATE
    LC_COLLATE=C

    local length="${#1}"
    for (( i = 0; i < length; i++ )); do
        local c="${1:i:1}"
        case $c in
            [a-zA-Z0-9.~_-]) printf "$c" ;;
            *) printf '%%%02X' "'$c" ;;
        esac
    done

    LC_COLLATE=$old_lc_collate
}
""")

        for variable, value in variable_order(env):
            f.write('export {}="{}"\n'.format(variable, value or ''))

    variables = 'unset ' + (' '.join(env.keys()))
    path = os.path.join(lamnfyc.settings.BASE_PATH, 'templates')
    files = [os.path.join(root, file) for root, dir, files in os.walk(path) for file in files]
    for file in files:
        file_path = os.path.join(lamnfyc.settings.environment_path, 'bin', os.path.basename(file))
        with open(file_path, 'w') as file_out:
            file_out.write(lamnfyc.utils.Template.from_file(file).safe_substitute(base_path=lamnfyc.settings.environment_path,
                                                                                  unset_variables=variables))
        st = os.stat(file_path)
        os.chmod(file_path, st.st_mode | stat.S_IEXEC)

    # generate all the packages we need to download
    downloads = []
    for package in environment_config['packages']:
        package = lamnfyc.utils.import_package(package['name'], package['version'])
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

        package.init(**package_item)
        package.expand()


def variable_order(items):
    FIND = re.compile('\$([\w]+)')
    ready = collections.OrderedDict()
    ready['VIRTUAL_ENV'] = None
    passes = 0
    while True:
        group = {}
        passes += 1
        for key, value in items.iteritems():
            if key in ready or key in group:
                continue

            if '$' in (value or ''):
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

        if len(items.keys()) == (len(ready.keys()) - 1):
            break
        elif passes > 10:
            raise Exception('Weird nesting going on')
