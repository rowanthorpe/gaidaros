#/usr/bin/env python
# encoding: utf-8
#
# This file is part of Gaidaros. See README.rst for more information.

'''Setup and build script for Gaidaros.'''

from __future__ import with_statement
from os.path import join as p_join, dirname as p_dirname, realpath as p_realpath, basename as p_basename, abspath as p_abspath, split as p_split, isdir as p_isdir, isfile as p_isfile, pardir as p_pardir

## EDIT - BEGIN ##
project_name = p_basename(p_abspath('.'))
project_description = 'Async server micro-framework for control freaks'
project_hosttype = 'github'
project_repotype = 'git'
project_username = 'rowanthorpe'
project_author = 'Rowan Thorpe'
project_author_email = 'rowan@rowanthorpe.com'
project_license = 'mit'
project_classifiers = [
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
]
project_keywords = ["async", "tcp", "server"]
## EDIT - END ##

## TEMPLATES - BEGIN ##
if project_license == 'mit':
    project_license_text = 'The MIT License: http://www.opensource.org/licenses/mit-license.php'
if project_hosttype == 'github':
    project_url_template = 'https://github.com/@username@/@name@'
    project_downloadurl_template = 'https://github.com/@username@/@name@/tarball/@version@'
if project_repotype == 'git':
    def project_update_version(fh_in, fh_out):
        import subprocess
        fh_out.write(re.sub('@version@', subprocess.Popen(["git", "describe", "--abbrev=0"], stdout=subprocess.PIPE).communicate()[0].rstrip('\n').rstrip('\r'), fh_in.read()))
## TEMPLATES - END ##

import sys, re
if __name__ == '__main__':
    if sys.argv[1] == 'set_version':
        exitval = 0
        lib_file = p_realpath(p_join(p_dirname(__file__), 'lib', project_name + '.py'))
        readme_file = p_realpath(p_join(p_dirname(__file__), 'README.rst'))
        if project_repotype == 'git':
            if not p_isdir(p_join(p_dirname(__file__), '.git')):
                sys.stderr.write("You tried to update the version information from {} but the repo files appear not to be in this directory.\n".format(project_repotype))
                exitval = 1
        else:
            sys.stderr.write("Repo type {} not implemented yet.\n".format(project_repotype))
            exitval = 1
        with open(lib_file + '.in', 'r') as fh_in:
            with open(lib_file, 'w') as fh_out:
                if len(sys.argv) > 2 and sys.argv[2]:
                    fh_out.write(re.sub('@version@', sys.argv[2], fh_in.read()))
                else:
                    project_update_version(fh_in, fh_out)
        with open(readme_file + '.in', 'r') as fh_in:
            with open(readme_file, 'w') as fh_out:
                if len(sys.argv) > 2 and sys.argv[2]:
                    fh_out.write(re.sub('@version@', sys.argv[2], fh_in.read()))
                else:
                    project_update_version(fh_in, fh_out)
        sys.exit(exitval)
    elif not p_isfile('lib/{}.py'.format(project_name)):
        sys.stderr.write("lib/{}.py doesn't yet exist. The maintainer should run python setup.py set_version before packaging this.\n".format(project_name))
        sys.exit(1)

sys.path.insert(0, p_realpath(p_join(p_dirname(__file__), 'lib')))
project_version = getattr(__import__(project_name, fromlist=['__version__']), '__version__')
sys.path.pop(0)
import os, shutil, tempfile, glob, sysconfig
from distutils.dir_util import mkpath
from distutils.command.install_data import install_data
from distutils.command.install_scripts import install_scripts
config_values = sysconfig.get_config_vars()
config_paths = sysconfig.get_paths()

#DEBUG
#print 'config_paths:'
#for x in config_paths.keys():
#    print ' ' + x + ' => ' + str(config_paths[x])
#print
#print 'config_values:'
#for x in config_values.keys():
#    print ' ' + x + ' => ' + str(config_values[x])

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
        _regex_sub_lines(p_join(config_paths['scripts'], 'run_' + project_name),
          ('^ *conf *=.*$',
           '    conf = "' + p_join(_conf_prefix, project_name, project_name + '.conf"')))

class MyInstallData(install_data):
    def run(self):
        ## Needed for virtualenvs, where @prefix@/local/etc seems to not exist as a symlink, like the other dirs...
        mkpath(p_join(_conf_prefix, project_name))
        install_data.run(self)
        _regex_sub_lines(p_join(_conf_prefix, project_name, project_name + '.conf'),
          ('^ *basedir *:.*$',
           'basedir: ' + config_values['base']),
          ('^ *root *=.*$',
           'root = %(basedir)s'),
          ('^ *lib *=.*$',
           'lib = ' + re.sub('^' + config_values['base'], '%(basedir)s', p_join(config_paths['purelib'], project_name))),
          ('^ *scripts *=.*$',
           'scripts = ' + re.sub('^' + config_values['base'], '%(basedir)s', config_paths['scripts'])),
          ('^ *run *=.*$',
           'run = ' + re.sub('^' + config_values['base'], '%(basedir)s', p_join(config_values['base'], 'run', project_name))),
          ('^ *configs *=.*$',
           'configs = ' + re.sub('^' + config_values['base'], '%(basedir)s', p_join(_conf_prefix, project_name))),
          ('^ *docs *=.*$',
           'docs = ' + re.sub('^' + config_values['base'], '%(basedir)s', p_join(config_values['base'], 'share', 'doc', project_name))))

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
    with open(p_join(p_dirname(__file__), file)) as f:
        val = f.read()
    return val

def _readlines_file_as_arr(file):
    with open(p_join(p_dirname(__file__), file)) as f:
        arr = map(lambda x: x.rstrip('\n').rstrip('\r'), f.readlines())
    return arr

## TODO: Will need _set_from_file as dict later, to support 'extras_require' for optional features
##       (e.g. Tornado frontend, etc)
#def _readlines_file_as_dict(file):
#    with open(p_join(p_dirname(__file__), file)) as f:
#        dict = map(lambda x: x.rstrip('\n').rstrip('\r'), f.readlines())
#        ... TODO ...
#    return dict

## TODO: Use proper python parsing => str, arr, or dict. Not readlines-type hacks.
def _set_from_file(file, dict, val, as_type):
    if as_type == 'array':
        dict[val] = _readlines_file_as_arr(file)
#    elif as_type == 'dict':
#        dict[val] = _readlines_file_as_dict(file)
    else:
        dict[val] = _read_file(file)

def main():
    _set_from_file('README.rst', METADATA, 'long_description', 'string')
    _set_from_file('requirements.txt', METADATA, 'requires', 'array')
## Don't need setuptools for now, using distutils only
#    _set_from_file('requirements.txt', SETUPTOOLS_METADATA, 'install_requires', 'array')
#    _set_from_file('extra_requirements.txt', SETUPTOOLS_METADATA, 'extras_require', 'dict')
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

## TODO: Add code to heuristically check if only directories in 'lib', then use _find_packages, otherwise just set package from package_name, and set its dir as 'lib'
## FIXME: This is a quick hack (doesn't recurse)
#def _find_packages(incl_tests=False):
#    for dir in glob.glob(p_join('lib','*')):
#        if p_isdir(dir) and p_isfile(p_join(dir, '__init__.py')):
#            if incl_tests or not (
#                dir == 'test' or dir[-5:] == '.test' or dir[:5] == 'test.' or re.match('\.test\.', dir)):
#                yield dir

METADATA = dict(
    cmdclass={"install_data": MyInstallData, "install_scripts": MyInstallScripts},
    name=project_name,
    version = project_version,
    provides=[project_name],
    description = project_description,
    author = project_author,
    author_email = project_author_email,
    url = re.sub('@name@', project_name, re.sub('@username@', project_username, project_url_template)),
    download_url = re.sub('@version@', project_version, re.sub('@name@', project_name, re.sub('@username@', project_username, project_downloadurl_template))),
    license = project_license_text,
    scripts = list(_files_glob('bin', ['*'])),
#    packages = list(_find_packages(incl_tests=False)),
#    package_data = {},
    packages = [project_name],
    package_dir = {project_name: 'lib'},
    data_files = [
        (p_join('share', 'doc', project_name), list(_files_glob('.', ['*.rst', '*.txt'])) + list(_files_glob(p_join('doc','share'), ['*.rst', '*.txt']))),
        (p_join('share', 'doc', project_name, 'examples'), list(_files_glob(p_join('doc', 'share', 'examples'), ['*.py', '*.sh']))),
        (p_join(_conf_prefix, project_name), list(_files_glob(p_join('etc', project_name), ['*.conf'])))
    ],
    classifiers = project_classifiers,
    keywords = project_keywords,
#    py_modules = [project_name], ## For smaller non-package modules...
#    maintainer = '', ## Not yet needed
#    maintainer_email = '', ## Not yet needed
#    platforms = [], ## Not yet needed
)

#SETUPTOOLS_METADATA = dict(
#    include_package_data = True,
#    zip_safe = False,
#    test_suite = '', ## TODO
#    entry_points = {}, ## Not yet needed
#)

if __name__ == '__main__':
    main()
