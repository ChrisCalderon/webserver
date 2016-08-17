from __future__ import print_function
from setuptools import setup
import os
import sys

if sys.version_info >= (3, 0):
    from functools import reduce


class SetupError(Exception):
    pass


def is_http(req):
    """Checks if a requirement is a link."""
    return req.startswith('http://') or req.startswith('https://')


def split_requirements(links_requirements, req):
    """Keeps track of requirements that aren't on PyPI."""
    links, requirements = links_requirements
    if is_http(req):
        i = req.find('#egg')
        links.append(req[:i])
        requirements.append(req[i+4:])
    else:
        requirements.append(req)
    return links, requirements


def read_metadata():
    """Finds the package to install and returns it's metadata."""
    subdirs = next(os.walk(os.getcwd()))[1]

    for subdir in subdirs:
        if '__init__.py' in os.listdir(subdir):
            print('Found package:', subdir)
            break
    else:
        raise SetupError('Can\'t find an __init__.py file!')

    metadata = {'name': subdir, 'packages': [subdir]}
    relevant_keys = {'__version__': 'version',
                     '__author__': 'author',
                     '__email__': 'author_email',
                     '__license__': 'license'}

    with open(os.path.join(subdir, '__init__.py')) as m:
        first_line = next(m)
        metadata['description'] = first_line.strip(). strip('"')
        for line in m:
            if len(relevant_keys) == 0:
                break
            for key in relevant_keys:
                if line.startswith(key):
                    break
            else:
                continue

            metadatum_name = relevant_keys.pop(key)
            __, info = line.split('=', 1)
            info = info.strip(' \n\'')
            metadata[metadatum_name] = info

    if relevant_keys:
        print('FYI; You didn\'t put the following info in your __init__.py:')
        print('   ', ', '.join(relevant_keys))

    return metadata


def parse_requirement_links():
    """Extracts dependency info from requirements.txt."""
    if not os.path.isfile('requirements.txt'):
        return {}
    
    with open('requirements.txt') as reqs:
        links, requirements = reduce(split_requirements,
                                     filter(None, map(str.strip, reqs)),
                                     [[], []])
    return {'dependency_links': links,
            'install_requires': requirements}


def simple_entry_point(metadata):
    """Makes a simple entry point for a __main__.main function."""
    name = metadata['packages'][0]
    main = os.path.join(name, '__main__.py')

    if not os.path.isfile(main):
        return {}

    with open(main, 'r') as m:
        for line in m:
            if line.startswith('def main():'):
                break
        else:
            return {}
        
    entry_fmt = '{} = {}.__main__:main'
    entry_point = entry_fmt.format(name, name)
    return {'entry_points': {'console_scripts': [entry_point]}}

metadata = read_metadata()
metadata.update(parse_requirement_links())
metadata.update(simple_entry_point(metadata))
setup(**metadata)
