#/usr/bin/env python
# encoding: utf-8
#
# This file is part of Gaidaros. See README.rst for more information.
#
# This setup.py and file hierarchy is from the setup-with-teeth project (v0.1.0):
#  https://github.com/rowanthorpe/setup-with-teeth
#  replace all [####] with your own text

'''Setup and build script for Gaidaros.'''

# FIXME(_find_packages()): Directory recursion (present version is a quick hack)
# FIXME: Add macro replacement based on python version
# FIXME: Make updating files with paths part of the build pass, not post-install
# FIXME: Make macro expansion in "run_XXXXXXX" file more explicit (at the moment is too intrusive)
# TODO: Recursive macro-expansion
# TODO: Multiple authors -> macros?
# TODO: Add more license types, host types, repo types, etc
# TODO(_find_packages()): Add code to heuristically check if there are only directories in 'lib', then use _find_packages, otherwise just set package from package_name, and set its dir as 'lib'
# TODO(_set_from_file()): Use proper python parsing => str, arr, or dict. Not readlines-type hacks.
# TODO(_readlines_file_as_dict()): Will need _set_from_file as dict later, to support 'extras_require' for optional features (e.g. Tornado frontend, etc)

from __future__ import with_statement
from os.path import join as p_join, dirname as p_dirname, realpath as p_realpath, basename as p_basename, abspath as p_abspath, split as p_split, isdir as p_isdir, isfile as p_isfile, pardir as p_pardir

## EDIT - BEGIN ##
project = {
    'description': 'Async server micro-framework for control freaks',
    'hosttype': 'github',
    'repotype': 'git',
    'username': 'rowanthorpe',
    'author': 'Rowan Thorpe',
    'author_email': 'rowan@rowanthorpe.com',
    'license': 'mit',
    'classifiers': [
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
    'keywords': ["async", "tcp", "server"],
    'macros_to_replace': ['name', 'username', 'description', 'author', 'author_email', 'license'],
}
project['name'] = p_basename(p_dirname(p_realpath(__file__)))
project['files_to_expand'] = p_join('lib', project['name'] + '.py'), 'README.rst', 'MANIFEST.in'
## EDIT - END ##

## TEMPLATES - BEGIN ##
if project['license'] == 'mit':
    project['license_text'] = 'The MIT License: http://www.opensource.org/licenses/mit-license.php'
else:
    project['license_text'] = 'none'
if project['hosttype'] == 'github':
    project['url_template'] = 'https://github.com/@username@/@name@'
    project['downloadurl_template'] = 'https://github.com/@username@/@name@/tarball/@version@'
elif project['hosttype'] == 'grnet':
    project['url_template'] = 'https://code.grnet.gr/projects/@name@'
    project['downloadurl_template'] = 'https://code.grnet.gr/git/@name@'
else:
    project['url_template'] = 'none'
    project['downloadurl_template'] = 'none'
## TEMPLATES - END ##

import sys, re
if __name__ == '__main__':
    if sys.argv[1] == 'macros':
        from os.path import getmtime as p_getmtime
        if len(sys.argv) > 2 and sys.argv[2]:
            project['version'] = sys.argv[2]
        else:
            if project['repotype'] == 'git':
                if not p_isdir(p_realpath(p_join(p_dirname(__file__), '.git'))):
                    sys.stderr.write("You tried to update version information but the repo files appear not to be in this directory.\n".format(project['repotype']))
                    sys.exit(1)
                import subprocess
                project['version'] = subprocess.Popen(['cd {} && git describe --abbrev=0'.format(p_realpath(p_dirname(__file__)))], stdout=subprocess.PIPE, shell=True).communicate()[0].rstrip('\n').rstrip('\r')
            else:
                sys.stderr.write("Repo type {} not implemented yet.\n".format(project['repotype']))
                sys.exit(1)
        for file_to_expand in project['files_to_expand']:
            file_to_expand = p_realpath(p_join(p_dirname(__file__), file_to_expand))
            if p_isfile(file_to_expand + '.in'):
                if p_isfile(file_to_expand) and p_getmtime(file_to_expand) > p_getmtime(file_to_expand + '.in'):
                    sys.stderr.write('WARNING: File to generate "{}" is already newer than input file "{}". "touch" the input file to override. Skipping.\n'.format(file_to_expand, file_to_expand + '.in'))
                else:
                    with open(file_to_expand + '.in', 'r') as fh_in:
                        file_content = fh_in.read()
                    project['macros_to_replace'].append('version')
                    for macro_to_replace in project['macros_to_replace']:
                        file_content = re.sub('@' + macro_to_replace + '@', project[macro_to_replace], file_content)
                    with open(file_to_expand, 'w') as fh_out:
                        fh_out.write(file_content)
            else:
                sys.stderr.write('WARNING: Specified file to expand "{}" does not have an input file "{}". Skipping.\n'.format(file_to_expand, file_to_expand + '.in'))
        sys.exit(0)
    else:
        for file_to_expand in project['files_to_expand']:
            file_to_expand = p_realpath(p_join(p_dirname(__file__), file_to_expand))
            if not p_isfile(file_to_expand):
                sys.stderr.write('"{}" doesn\'t yet exist. The maintainer should run "python setup.py macros" before packaging this.\n'.format(file_to_expand))
                sys.exit(1)

sys.path.insert(0, p_realpath(p_join(p_dirname(__file__), 'lib')))
project['version'] = getattr(__import__(project['name'], fromlist=['__version__']), '__version__')
sys.path.pop(0)
import os, shutil, tempfile, glob, sysconfig
from distutils.dir_util import mkpath
from distutils.command.install_data import install_data
from distutils.command.install_scripts import install_scripts
config_values = sysconfig.get_config_vars()
config_paths = sysconfig.get_paths()
## NB: Don't just check '/usr', to allow for virtualenvs
if p_basename(config_paths['data']) == 'usr':
    ## installing to "/usr", so "etc" -> "/etc" (not to /usr/etc, to be FHS friendly)
    _conf_prefix = p_join(config_paths['data'], p_pardir, 'etc')
else:
    ## installing to "somewhere_else", so "etc" -> "somewhere_else/etc"
    _conf_prefix = p_join(config_paths['data'], 'etc')

class MyInstallScripts(install_scripts):
    def run(self):
        install_scripts.run(self)
        _regex_sub_lines(p_join(config_paths['scripts'], 'run_' + project['name']),
          ('^ *conf *=.*$',
           '    conf = "' + p_join(_conf_prefix, project['name'], project['name'] + '.conf"')))

class MyInstallData(install_data):
    def run(self):
        ## Needed for virtualenvs, where @prefix@/local/etc seems to not exist as a symlink, like the other dirs...
        mkpath(p_join(_conf_prefix, project['name']))
        install_data.run(self)
        _regex_sub_lines(p_join(_conf_prefix, project['name'], project['name'] + '.conf'),
          ('^ *basedir *:.*$',
           'basedir: ' + config_values['base']),
          ('^ *root *=.*$',
           'root = %(basedir)s'),
          ('^ *lib *=.*$',
           'lib = ' + re.sub('^' + config_values['base'], '%(basedir)s', p_join(config_paths['purelib'], project['name']))),
          ('^ *scripts *=.*$',
           'scripts = ' + re.sub('^' + config_values['base'], '%(basedir)s', config_paths['scripts'])),
          ('^ *run *=.*$',
           'run = ' + re.sub('^' + config_values['base'], '%(basedir)s', p_join(config_values['base'], 'run', project['name']))),
          ('^ *configs *=.*$',
           'configs = ' + re.sub('^' + config_values['base'], '%(basedir)s', p_join(_conf_prefix, project['name']))),
          ('^ *docs *=.*$',
           'docs = ' + re.sub('^' + config_values['base'], '%(basedir)s', p_join(config_values['base'], 'share', 'doc', project['name']))))

def _regex_sub_lines(file_path, *pat_subs):
    fh, abs_path = tempfile.mkstemp()
    with open(file_path, 'r') as old_file:
        with open(abs_path, 'w') as new_file:
            for line in old_file.readlines():
                line = line.rstrip('\r?\n')
                for pattern, subst in pat_subs:
                    line = re.sub(pattern, subst, line)
                new_file.write(line + '\n')
    os.close(fh)
    os.chmod(abs_path,os.stat(file_path)[0])
    os.remove(file_path)
    shutil.move(abs_path, file_path)

def _files_glob(path, globs, on_sys_prefix=False, trim_prefix=False):
    if on_sys_prefix:
        leadpath = p_realpath(p_join(sys.prefix, path))
    else:
        leadpath = p_realpath(path)
    result = []
    for blob in globs:
        tmp_result = glob.glob(p_join(leadpath, blob))
        if trim_prefix:
            result.extend(lambda x: x.lstrip(leadpath), tmp_result)
        else:
            result.extend(tmp_result)
    return result

def _read_file(file):
    with open(p_realpath(p_join(p_dirname(__file__), file))) as f:
        val = f.read()
    return val

def _readlines_file_as_array(file):
    with open(p_realpath(p_join(p_dirname(__file__), file))) as f:
        arr = map(lambda x: x.rstrip('\n').rstrip('\r'), f.readlines())
    return arr

#def _readlines_file_as_dict(file):
#    with open(p_realpath(p_join(p_dirname(__file__), file))) as f:
#        dict = map(lambda x: x.rstrip('\n').rstrip('\r'), f.readlines())
#        ...
#    return dict

def _set_from_file(file, dict, val, as_type):
    if as_type == 'array':
        dict[val] = _readlines_file_as_array(file)
#    elif as_type == 'dict':
#        dict[val] = _readlines_file_as_dict(file)
    else:
        dict[val] = _read_file(file)

def main():
    _set_from_file('README.rst', METADATA, 'long_description', 'string')
    _set_from_file('requirements.txt', METADATA, 'requires', 'array')
## NB: Don't need setuptools for now, using distutils only
#    _set_from_file('requirements.txt', SETUPTOOLS_METADATA, 'install_requires', 'array')
#    _set_from_file('requirements_extra.txt', SETUPTOOLS_METADATA, 'extras_require', 'dict')
#    try:
#        from setuptools import setup #, find_packages - I do my own version of find_packages now
#        SETUPTOOLS_METADATA['packages'] = find_packages(exclude=["*.test", "*.test.*", "test.*", "test"])
#        METADATA.update(SETUPTOOLS_METADATA)
#    except ImportError:
#        from distutils.core import setup
#        if sys.version < '2.2.3':
#            from distutils.dist import DistributionMetadata
#            DistributionMetadata.classifiers = None
#            DistributionMetadata.download_url = None
    from distutils.core import setup
    if sys.version < '2.2.3':
        from distutils.dist import DistributionMetadata
        DistributionMetadata.classifiers = None
        DistributionMetadata.download_url = None
    setup(**METADATA)

#def _find_packages(incl_tests=False):
#    for dir in glob.glob(p_join('lib','*')):
#        if p_isdir(dir) and p_isfile(p_join(dir, '__init__.py')):
#            if incl_tests or not (
#                dir == 'test' or dir[-5:] == '.test' or dir[:5] == 'test.' or re.match('\.test\.', dir)):
#                yield dir

METADATA = {
    'cmdclass': {"install_data": MyInstallData, "install_scripts": MyInstallScripts},
    'name': project['name'],
    'version': project['version'],
    'provides': [project['name']],
    'description': project['description'],
    'author': project['author'],
    'author_email': project['author_email'],
    'license': project['license_text'],
    'scripts': list(_files_glob('bin', ['*'])),
#    'packages': list(_find_packages(incl_tests=False)),
#    'package_data': {},
    'packages': [project['name']],
    'package_dir': {project['name']: 'lib'},
    'data_files': [
        (p_join('share', 'doc', project['name']), list(_files_glob('.', ['*.rst', '*.txt'])) + list(_files_glob(p_join('doc','share'), ['*.rst', '*.txt']))),
        (p_join('share', 'doc', project['name'], 'examples'), list(_files_glob(p_join('doc', 'share', 'examples'), ['*.py', '*.sh']))),
        (p_join(_conf_prefix, project['name']), list(_files_glob(p_join('etc', project['name']), ['*.conf'])))
    ],
    'classifiers': project['classifiers'],
    'keywords': project['keywords'],
#    'py_modules': [project['name']], ## For smaller non-package modules...
#    'maintainer': '', ## Not yet needed
#    'maintainer_email': '', ## Not yet needed
#    'platforms': [], ## Not yet needed
}
METADATA['url'] = project['url_template']
METADATA['download_url'] = project['downloadurl_template']
for macro_to_expand in ['name', 'username', 'version', 'hosttype', 'repotype']:
    METADATA['url'] = re.sub('@' + macro_to_expand + '@', project[macro_to_expand], METADATA['url'])
    METADATA['download_url'] = re.sub('@' + macro_to_expand + '@', project[macro_to_expand], METADATA['download_url'])

#SETUPTOOLS_METADATA = {
#    'include_package_data': True,
#    'zip_safe': False,
#    'test_suite': '', ## TODO
#    'entry_points': {}, ## Not yet needed
#}

if __name__ == '__main__':
    main()
