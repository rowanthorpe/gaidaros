#/usr/bin/env python
# encoding: utf-8
from __future__ import unicode_literals, with_statement

'''Setup and build script for Gaidaros.'''

#
# See README.rst for more information.
#
# This setup.py and file hierarchy is from the setup-with-teeth project (v0.2.6):
#  https://github.com/rowanthorpe/setup-with-teeth
#  replace all XXXXXXX with your own text

# FIXME: Make updating files with paths part of the build pass, not post-install
# FIXME: Make macro expansion in "bin/XXXXXXX" file more explicit (at the moment is too intrusive)
# FIXME: Generate project name from directory (even in virtualenv, pip, etc)
# TODO: add logic for using more vars from projects[], e.g. package_data, etc
# TODO: add more hosttypes to templates section
# TODO: Recursive macro-expansion
# TODO: Multiple authors -> iterable macros?
# TODO: Add more license types, host types, repo types, etc
# TODO(_set_dict_from_file()): Use proper python parsing => str, arr, or dict. Not readlines-type hacks.

if __name__ != '__main__':
    raise RuntimeError('This script should only be run directly. It is not a library.')

import os, sys, shutil, tempfile, glob, sysconfig, re, fcntl, subprocess, importlib
from os.path import join as p_join, dirname as p_dirname, realpath as p_realpath, basename as p_basename, \
                    isdir as p_isdir, isfile as p_isfile, pardir as p_pardir, getmtime as p_getmtime, \
                    normpath as p_normpath, splitdrive as p_splitdrive
from distutils.dir_util import mkpath as d_mkpath
from distutils.command.install_data import install_data as d_install_data
from distutils.command.install_scripts import install_scripts as d_install_scripts
from distutils.core import setup
from distutils.dist import DistributionMetadata

## GLOBAL VARS SETUP ##

_newdirsep = p_realpath('.')
_dirsep = ''
while _newdirsep != _dirsep: # iterate to find '/' or the system equivalent
    _dirsep = _newdirsep
    _newdirsep = p_dirname(_dirsep)
_dirsep = p_splitdrive(_dirsep)[1]
del _newdirsep
_projectpath = p_realpath('.')
_configvars = sysconfig.get_config_vars()
_configpaths = sysconfig.get_paths()
if p_basename(_configpaths['data']) == 'usr': #GOTCHA: '[path]/usr', not only '/usr', to allow for virtualenvs...
    _configprefix = p_normpath(p_join(_configpaths['data'], p_pardir, 'etc')) # "[path]/usr" => "[path]/etc" ("[path]/usr/etc", FHS-friendly)
else:
    _configprefix = p_join(_configpaths['data'], 'etc') # "[path]/[something_else]" => "[path]/[something_else]/etc"
_dirsep, _projectpath, _configprefix = unicode(_dirsep), unicode(_projectpath), unicode(_configprefix)

## TO EDIT ##

project = {
    'description': 'Async server micro-framework for control freaks',
    'hosttype': 'github',
    'repotype': 'git',
    'username': 'rowanthorpe',
    'author': 'Rowan Thorpe',
    'author_email': 'rowan@rowanthorpe.com',
    'classifiers': [
        'Development Status :: 3 - Alpha',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Clustering',
        'Topic :: System :: Hardware :: Symmetric Multi-processing',
        'Topic :: System :: Networking',
    ],
    'keywords': ["async", "tcp", "server"],
    'macros_to_replace': ['name', 'username', 'description', 'author', 'author_email', 'version'],
    'license': None,          #NB: "...", if needed (not in classifiers)
    'py_modules': None,       #NB: [...], if needed
    'maintainer': None,       #NB: "...", if needed
    'maintainer_email': None, #NB: "...", if needed
    'platforms': None,        #NB: [...], if needed
}

## MAY BE EDITED ##

#project['name'] = unicode(p_basename(_projectpath)) #FIXME: doesn't play nice with virtualenv
project['name'] = 'gaidaros'
if p_join(_projectpath, 'lib') not in sys.path:
    sys.path.insert(0, p_join(_projectpath, 'lib'))
project.update({
    'files_to_expand': (p_join('lib', project['name'] + '.py'), 'README.rst'),
    'version': getattr(importlib.import_module(project['name']), '__version__'),
})
del sys.path[0]

## TEMPLATES ##

if project['hosttype'] == 'github':
    project['url_template'] = 'https://github.com/@username@/@name@'
    project['download_url_template'] = 'https://github.com/@username@/@name@/tarball/@version@'
#if project['license'] == '[weird unknown license]':
#    project['license_text'] = 'The [weird unknown] License: [url]'

## FUNCTIONS ##

def _files_glob(path, globs, trim_prefix='', realpath=False):
    if not path:
        path = '.'
    if realpath:
        path = p_realpath(path)
        if trim_prefix:
            trim_prefix = p_realpath(trim_prefix)
    elif trim_prefix:
        trim_prefix = p_normpath(trim_prefix)
    for globlet in globs:
        globresults = glob.glob(p_normpath(p_join(path, globlet)))
        for globresult in globresults:
            if trim_prefix and len(trim_prefix + _dirsep) < len(globresult) and globresult[:len(trim_prefix + _dirsep)] == trim_prefix + _dirsep:
                result = globresult[len(trim_prefix + _dirsep):]
            else:
                result = globresult
            yield unicode(result)

def _files_glob_l(*args, **kws):
    return list(_files_glob(*args, **kws))

def _find_dirs(topdir='lib'):
    if p_isdir(topdir):
        for _dir in os.walk(topdir):
            if p_isfile(p_join(_dir[0], '__init__.py')):
                yield _dir[0]

def _pkg_mappings(*args, **kws):
    yield project['name'], 'lib'
    for _dir in _find_dirs(*args, **kws):
        if _dir != 'lib':
            yield project['name'] + '.' + _dir[len('lib' + _dirsep):].replace(_dirsep, '.'), _dir # remove leading "lib/" and do s:/:.:g

def _regex_sub_lines(file_path, *pat_subs):
    fh, abs_path = tempfile.mkstemp()
    fcntl.lockf(fh, fcntl.LOCK_EX)
    with open(file_path, 'r') as old_file:
        with open(abs_path, 'w') as new_file:
            fcntl.lockf(new_file, fcntl.LOCK_EX)
            for line in old_file.readlines():
                line = line.rstrip('\r?\n')
                for pattern, subst in pat_subs:
                    line = re.sub(pattern, subst, line)
                new_file.write(line + '\n')
    fcntl.lockf(fh, fcntl.LOCK_UN)
    os.close(fh)
    os.chmod(abs_path,os.stat(file_path)[0])
    os.remove(file_path)
    shutil.move(abs_path, file_path)

def _read_file(file):
    with open(file) as f:
        val = f.read()
    return val

def _readlines_file_as_array(file):
    with open(file) as f:
        arr = [x.rstrip('\r?\n') for x in f.readlines()]
    return arr

def _readlines_file_as_dict(file):
    return dict(x.split(' ', 1) for x in _readlines_file_as_array(file))

def _set_dict_from_file(file, _dict, val, as_type):
    if as_type == 'array':
        _dict[val] = _readlines_file_as_array(file)
    elif as_type == 'dict':
        _dict[val] = _readlines_file_as_dict(file)
    else:
        _dict[val] = _read_file(file)

## OVERRIDE CLASSES ##

class MyInstallScripts(d_install_scripts):
    def run(self):
        d_install_scripts.run(self)
        _regex_sub_lines(p_join(_configpaths['scripts'], project['name']),
          (r'@configfile@',
           '"' + p_join(_configprefix, project['name'], project['name'] + r'.conf"')))

class MyInstallData(d_install_data):
    def run(self):
        d_mkpath(p_join(_configprefix, project['name'])) #GOTCHA: needed for virtualenvs, @prefix@/etc sometimes doesn't exist (even as symlink)
        d_install_data.run(self)
        _regex_sub_lines(p_join(_configprefix, project['name'], project['name'] + '.conf'),
          (r'^( *)basedir *:.*$',
           r'\1basedir: ' + _configvars['base']),
          (r'^( *)root *=.*$',
           r'\1root = %(basedir)s'),
          (r'^( *)lib *=.*$',
           r'\1lib = ' + re.sub(r'^' + _configvars['base'], r'%(basedir)s', p_join(_configpaths['purelib'], project['name']))),
          (r'^( *)scripts *=.*$',
           r'\1scripts = ' + re.sub(r'^' + _configvars['base'], r'%(basedir)s', _configpaths['scripts'])),
          (r'^( *)run *=.*$',
           r'\1run = ' + re.sub(r'^' + _configvars['base'], r'%(basedir)s', p_join(_configvars['base'], 'run', project['name']))),
          (r'^( *)configs *=.*$',
           r'\1configs = ' + re.sub(r'^' + _configvars['base'], r'%(basedir)s', p_join(_configprefix, project['name']))),
          (r'^( *)docs *=.*$',
           r'\1docs = ' + re.sub(r'^' + _configvars['base'], r'%(basedir)s', p_join(_configvars['base'], 'share', 'doc', project['name']))))

## MAIN ##

if sys.argv[1] == 'macros':
    if len(sys.argv) > 2 and sys.argv[2]:
        project['version'] = sys.argv[2]
    else:
        #NB: default to bumping the version up by one patch level, e.g.: 0.1.2 -> 0.1.3
        #    to bump a minor or major level, specify the version string manually as second arg instead
        if project['repotype'] == 'git':
            if not p_isdir('.git'):
                sys.stderr.write("You tried to update version information but the repo files appear not to be in this directory.\n".format(project['repotype']))
                sys.exit(1)
            _projectversionstr = subprocess.Popen(['git describe --abbrev=0'], stdout=subprocess.PIPE, shell=True).communicate()[0].rstrip('\r?\n').split('.')
        else:
            sys.stderr.write("Repo type {} not implemented yet.\n".format(project['repotype']))
            sys.exit(1)
        project['version'] = '.'.join(_projectversionstr[:-1] + [unicode(int(_projectversionstr[-1]) + 1)])
    for file_to_expand in project['files_to_expand']:
        file_to_expand = p_join('.', file_to_expand)
        if p_isfile(file_to_expand + '.in'):
            if p_isfile(file_to_expand) and p_getmtime(file_to_expand) > p_getmtime(file_to_expand + '.in'):
                sys.stderr.write('WARNING: File to generate "{}" is already newer than input file "{}". "touch" the input file to override. Skipping.\n'.format(file_to_expand, file_to_expand + '.in'))
            else:
                with open(file_to_expand + '.in', 'r') as fh_in:
                    file_content = fh_in.read().decode('utf-8')
                for macro_to_replace in project['macros_to_replace']:
                    file_content = re.sub(r'@' + macro_to_replace + r'@', project[macro_to_replace], file_content)
                with open(file_to_expand, 'w') as fh_out:
                    fcntl.lockf(fh_out, fcntl.LOCK_EX)
                    fh_out.write(file_content.encode('utf-8'))
        else:
            sys.stderr.write('WARNING: Specified file to expand "{}" does not have an input file "{}". Skipping.\n'.format(file_to_expand, file_to_expand + '.in'))
else:
    METADATA = {
        'cmdclass': {"install_data": MyInstallData, "install_scripts": MyInstallScripts},
        'name': str(project['name']), #GOTCHA: name must be a bytestring, even in unicode environment
        'version': project['version'],
        'provides': [project['name']],
        'description': project['description'],
        'author': project['author'],
        'author_email': project['author_email'],
        'scripts': _files_glob_l('bin', ('*',)),
        'data_files': [
            (p_join('share', 'doc', project['name']),
                _files_glob_l('.', ('*.rst', '*.txt'), trim_prefix='.') +
                _files_glob_l(p_join('doc','share'), ('*.rst', '*.txt', '*.pdf', '*.html'))),
            (p_join('share', 'doc', project['name'], 'examples'),
                _files_glob_l(p_join('doc', 'share', 'examples'), ('*.py', '*.sh'))),
            (p_join(_configprefix, project['name']),
                _files_glob_l(p_join('etc', project['name']), ('*.conf',))),
        ],
        'package_dir': dict(_pkg_mappings()),
        'package_data': {},
        'classifiers': project['classifiers'],
        'keywords': project['keywords'],
        'url': project['url_template'],
        'download_url': project['download_url_template'],
    }
    for _val in 'license', 'py_modules', 'maintainer', 'maintainer_email', 'platforms':
        if project[_val] is not None:
            METADATA[_val] = project[_val]
    for _man_section in xrange(1,9):
        _these_files = _files_glob_l(p_join('doc', 'man'), ('*.' + unicode(_man_section),))
        if _these_files:
            METADATA['data_files'] += (p_join('share', 'man', 'man' + unicode(_man_section)), _these_files)
    METADATA['packages'] = map(str, METADATA['package_dir'].keys())
    for _dir in METADATA['package_dir']:
        if p_isdir(p_join(METADATA['package_dir'][_dir], 'data')):
            _these_files = _files_glob_l(p_join(METADATA['package_dir'][_dir], 'data'), ('*.rst', '*.txt', '*.pdf', '*.html'))
            if _these_files:
                METADATA['package_data'][_dir] = _these_files
    for macro_to_expand in ['name', 'username', 'version', 'hosttype', 'repotype']:
        METADATA['url'] = re.sub(r'@' + macro_to_expand + r'@', project[macro_to_expand], METADATA['url'])
        METADATA['download_url'] = re.sub(r'@' + macro_to_expand + r'@', project[macro_to_expand], METADATA['download_url'])
    _set_dict_from_file('README.rst', METADATA, 'long_description', 'string')
    _set_dict_from_file('requirements.txt', METADATA, 'requires', 'array')

#NB: Don't need setuptools for now, using distutils only, but if used it would need something like:
#    try:
#        from setuptools import setup #, find_packages #NB: I do my own version of find_packages now
#        SETUPTOOLS_METADATA = {
#            'packages': find_packages(exclude=["*.test", "*.test.*", "test.*", "test"]),
#            'include_package_data': True,
#            'zip_safe': False,
#            'test_suite': '', #Not yet used
#            'entry_points': {}, #Not yet needed
#        }
#        _set_dict_from_file(....?, SETUPTOOLS_METADATA, 'install_requires', 'array')
#        _set_dict_from_file('requirements_extra.txt', SETUPTOOLS_METADATA, 'extras_require', 'dict')
#        METADATA.update(SETUPTOOLS_METADATA)
#    except ImportError:
#        if sys.version < '2.2.3':
#            DistributionMetadata.classifiers = None
#            DistributionMetadata.download_url = None

    if sys.version < '2.2.3':
        DistributionMetadata.classifiers = None
        DistributionMetadata.download_url = None

#DEBUG: begin
#    import pprint
#    pp = pprint.PrettyPrinter(indent=4)
#    pp.pprint(METADATA)
#    exit(0)
#DEBUG: end

    try:
        os.remove('MANIFEST') #GOTCHA: if this is present it doesn't get overwritten from present data
    except OSError:
        pass
    setup(**METADATA)

sys.exit(0)
