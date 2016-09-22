import os
# import sys
import yaml
import argparse
import pkg_resources
import logging
import concurrent.futures

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
    lamnfyc.settings.environment_path = os.path.join(os.path.abspath(os.path.curdir), args.environment)

    # if os.path.isdir(args.environment):
    #     log.fatal('ERROR: File already exists and is not a directory.')
    #     log.fatal('Please provide a different path or delete the file.')
    #     sys.exit(3)
    #
    # # create the cache dir if its missing
    # if not os.path.isdir(lamnfyc.settings.CACHE_PATH):
    #     os.mkdir(lamnfyc.settings.CACHE_PATH)
    #
    # # make sure all the paths exists
    # os.mkdir(args.environment)
    # os.mkdir(os.path.join(args.environment, 'lib'))
    # os.mkdir(os.path.join(args.environment, 'bin'))
    # os.mkdir(os.path.join(args.environment, 'share'))
    # os.mkdir(os.path.join(args.environment, 'include'))

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
