#!/usr/bin/env python
"""
Check if the requirement versions match between all packages -- otherwise whats going on? which one do we use, this is
not the wild-wild-west -- we have rules
"""
import sys
import os
import re
import logging

from pip.req import parse_requirements
from itertools import chain
from collections import defaultdict
from argparse import ArgumentParser
from functools import partial

log = logging.getLogger(__file__)
if not log.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    log.addHandler(console)

__version__ = '0.0.1'

# try to find the pattern "-r <path> (line #)" from the requirement files
RE_MATCH = re.compile(r'-r ([^\(]+) \(')


def main():
    parser = ArgumentParser(description='Check mismatch requirement. v.{}'.format(__version__))
    parser.add_argument('requirements', nargs='+', help='path to the requirements file')

    args, vargs = parser.parse_known_args()

    # paste together all the requirement files
    generator = chain(*[parse_requirements(req, session=False) for req in args.requirements])
    # defaultdict that has a defaultdict of sets: {'..': {'..': set()}}
    parsed = defaultdict(lambda : defaultdict(set))
    # loop over all that are not links (i.e. git links)
    for requirement in [x for x in generator if x.link is None]:
        if '==' in str(requirement.req):
            name, version = str(requirement.req).split('==')
        elif requirement.req.specifier == '':
            name = str(requirement.req)
            version = 'x.x.x'
            log.warn('{} doens\'t have a specified version'.format(name))
        else:
            # only test what we can compare... (some are like this and its hard.. "django>=1.8.5,<1.9")
            continue
        parsed[name]['versions'].add(version)
        parsed[name][version].add(requirement)
    errors = []
    for key, value in parsed.iteritems():
        # if there is less than 2 entries, there is no error
        if len(value['versions']) < 2:
            continue
        # add the main header file
        errors.append('  * {} as ({})'.format(key, ', '.join(value['versions'])))
        for version in value['versions']:
            # loop over all the requirement entries per verion (fun fact: you can have more than 1)
            for requirement in value[version]:
                comes_from = requirement.comes_from
                # try to see if we can present the user with a nicer path, an absolute path
                match = RE_MATCH.match(comes_from)
                if match:
                    original_path = match.groups()[0]
                    # replace the original, ugly [relative] path with a pretty absolute one
                    comes_from = comes_from.replace(original_path, os.path.abspath(original_path))
                errors.append('    - {} from {}'.format(version, comes_from))
    if errors:
        print "There are some conflits between the {} code repositories we have:\a".format(len(args.requirements))
        print '\n'.join(errors)
        sys.exit(1)


if __name__ == '__main__':
    main()
