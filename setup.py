#/usr/bin/env python
# encoding: utf-8
#
# This file is part of Gaidaros. See README.rst for more information.

'''Setup and build script for Gaidaros.'''

import os, sys, shutil, tempfile, re, glob
from distutils.command.install_data import install_data
from distutils.command.install_scripts import install_scripts
from os.path import join as pjoin
from os.path import dirname as pdirname
from os.path import isdir as pisdir
from os.path import isfile as pisfile
from os.path import realpath as prealpath

sys.path.insert(0, prealpath(pjoin(pdirname(__file__), 'gaidaros')))
from gaidaros import __version__
sys.path.pop(0)

def _regex_sub_lines(file_path, *pat_subs):
    fh, abs_path = tempfile.mkstemp()
    with open(abs_path, 'w') as new_file:
        with open(file_path, 'r') as old_file:
            for line in old_file:
                line = line.rstrip('\r?\n')
                for pattern, subst in pat_subs:
                    line = re.sub(pattern, subst, line)
                new_file.write(line + '\n')
    os.close(fh)
    os.chmod(abs_path,os.stat(file_path)[0])
    os.remove(file_path)
    shutil.move(abs_path, file_path)

# TODO: see if there is a more automated way of specifying the python-lib path
class post_install_d(install_data):
    def run(self):
        install_data.run(self)
        _regex_sub_lines(
            pjoin(sys.prefix, 'etc', 'gaidaros', 'gaidaros.conf'),
            ('^basedir ?:.*$', 'basedir: ' + sys.prefix),
            ('^lib ?=.*$',
             'lib = %(basedir)s/lib/python{}.{}/site-packages/gaidaros'.format(
                 sys.version_info[0], sys.version_info[1])))

class post_install_s(install_scripts):
    def run(self):
        install_scripts.run(self)
        _regex_sub_lines(
            pjoin(sys.prefix, 'bin', 'run_gaidaros'),
            ("^    conf = '/etc/gaidaros/gaidaros.conf'$",
             "    conf = '" + sys.prefix + "/etc/gaidaros/gaidaros.conf'"))


def _in_dir(dirpath, files):
    return map(lambda x: pjoin(*(dirpath + [x])), files)

def _files_glob(path, globpatt, on_sys_prefix=False, trim_path=False):
    if on_sys_prefix:
        leadpath = prealpath(pjoin(*([sys.prefix] + path)))
    else:
        leadpath = prealpath(pjoin(*path))
    result = glob.glob(pjoin(leadpath, globpatt))
    if trim_path:
        return map(lambda x: x.lstrip(leadpath), result)
    else:
        return result

#quick hack (doesn't recurse yet)
def _find_packages(incl_tests=False):
    for dir in glob.glob('*'):
        if pisdir(dir) and pisfile(pjoin(dir, '__init__.py')):
            if incl_tests or not (
                dir == 'test' or dir[-5:] == '.test' or dir[:5] == 'test.' or re.match('\.test\.', dir)):
                yield dir

METADATA = dict(
    cmdclass={"install_data": post_install_d, "install_scripts": post_install_s},
    name='gaidaros',
    version = __version__,
    description = 'Async server micro-framework for control freaks',
    author = 'Rowan Thorpe',
    author_email = 'rowan@rowanthorpe.com',
    url = 'http://github.com/rowanthorpe/gaidaros',
    download_url = 'https://api.github.com/repos/rowanthorpe/gaidaros/tarball/' + __version__,
    license = 'The MIT License: http://www.opensource.org/licenses/mit-license.php',
    packages = list(_find_packages(incl_tests=False)),
    scripts = _files_glob(['bin'], '*'),
    data_files = [
        (pjoin('etc', 'gaidaros'), _files_glob(['gaidaros', 'stuff'], '*.conf')),
        (pjoin('usr', 'share', 'doc', 'gaidaros'), ['LICENSE.txt', 'README.rst'] + _files_glob(['docs'], '*.rst')),
        (pjoin('usr', 'share', 'doc', 'gaidaros', 'examples'),
         _files_glob(['examples'], '*.py') + _files_glob(['examples'], '*.sh')),
    ],
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Clustering',
        'Topic :: System :: Hardware :: Symmetric Multi-processing',
        'Topic :: System :: Networking',
    ],
    keywords = ["async", "tcp", "server"],
#    package_dir = {'gaidaros': 'gaidaros'}, ## redundant?
#    py_modules = ['gaidaros'], ## redundant?
#    maintainer = '', ## not yet needed
#    maintainer_email = '', ## not yet needed
#    platforms = [], ## not yet needed
)

SETUPTOOLS_METADATA = dict(
#    include_package_data = True,
#    package_data = {'gaidaros': ['stuff/*']}, ## better having this installed to /etc by data_files?
#    zip_safe = False,
#    test_suite = '', ##TODO
#    entry_points = {}, ## not yet needed
)

def read_file(file):
    with open(pjoin(pdirname(__file__), file)) as f:
        val = f.read()
    return val

def readlines_file_as_arr(file):
    with open(pjoin(pdirname(__file__), file)) as f:
        arr = map(lambda x: x.rstrip('\n').rstrip('\r'), f.readlines())
    return arr

## TODO: will need set_from_file as dict later, to support 'extras_require' for optional features
##       (e.g. Tornado frontend, etc)
#def readlines_file_as_dict(file):
#    with open(pjoin(pdirname(__file__), file)) as f:
#        dict = map(lambda x: x.rstrip('\n').rstrip('\r'), f.readlines())
#        ... TODO ...
#    return dict

def set_from_file(file, dict, val, as_type):
    if as_type == 'array':
        dict[val] = readlines_file_as_arr(file)
#    elif as_type == 'dict':
#        dict[val] = readlines_file_as_dict(file)
    else:
        dict[val] = read_file(file)

def main():
    set_from_file('README.rst', METADATA, 'long_description', 'string')
    set_from_file('requirements.txt', SETUPTOOLS_METADATA, 'install_requires', 'array')
#    set_from_file('extras_requirements.txt', SETUPTOOLS_METADATA, 'extras_require', 'dict')
    try:
        from setuptools import setup, find_packages
        ## I do my own version of this now
#        SETUPTOOLS_METADATA['packages'] = find_packages(exclude=["*.test", "*.test.*", "test.*", "test"])
        METADATA.update(SETUPTOOLS_METADATA)
    except ImportError:
        from distutils.core import setup
    setup(**METADATA)

if __name__ == '__main__':
    main()
