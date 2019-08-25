import codecs
import os
import pathlib
import re
import sys
from distutils.command.build_ext import build_ext
from distutils.errors import (CCompilerError, DistutilsExecError,
                              DistutilsPlatformError)

from setuptools import Extension, setup


if sys.version_info < (3, 5, 3):
    raise RuntimeError("frozenlist 1.x requires Python 3.5.3+")


NO_EXTENSIONS = bool(os.environ.get('FROZENLIST_NO_EXTENSIONS'))  # type: bool

if sys.implementation.name != "cpython":
    NO_EXTENSIONS = True


here = pathlib.Path(__file__).parent

# NOTE: makefile cythonizes all Cython modules

extensions = [
    Extension('frozenlist._frozenlist', ['frozenlist/_frozenlist.c'])
]


class BuildFailed(Exception):
    pass


class ve_build_ext(build_ext):
    # This class allows C extension building to fail.

    def run(self):
        try:
            build_ext.run(self)
        except (DistutilsPlatformError, FileNotFoundError):
            raise BuildFailed()

    def build_extension(self, ext):
        try:
            build_ext.build_extension(self, ext)
        except (CCompilerError, DistutilsExecError,
                DistutilsPlatformError, ValueError):
            raise BuildFailed()


txt = (here / 'frozenlist' / '__init__.py').read_text('utf-8')
try:
    version = re.findall(r"^__version__ = '([^']+)'\r?$",
                         txt, re.M)[0]
except IndexError:
    raise RuntimeError('Unable to determine version.')

install_requires = []


def read(f):
    return (here / f).read_text('utf-8').strip()


args = dict(
    name='frozenlist',
    version=version,
    description=(
        'A list-like structure which implements '
        'collections.abc.MutableSequence'
    ),
    long_description='\n\n'.join((read('README.rst'), read('CHANGES.rst'))),
    long_description_content_type="text/x-rst",
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Development Status :: 5 - Production/Stable',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
    ],
    author='Nikolay Kim',
    author_email='fafhrd91@gmail.com',
    maintainer='Martijn Pieters <mj@zopatista.com>',
    maintainer_email='aio-libs@googlegroups.com',
    url='https://github.com/aio-libs/frozenlist',
    project_urls={
        'Chat: Gitter': 'https://gitter.im/aio-libs/Lobby',
        'CI: AppVeyor': 'https://ci.appveyor.com/project/aio-libs/frozenlist',
        'CI: Circle': 'https://circleci.com/gh/aio-libs/frozenlist',
        'CI: Shippable': 'https://app.shippable.com/github/aio-libs/frozenlist',
        'CI: Travis': 'https://travis-ci.com/aio-libs/frozenlist',
        'Coverage: codecov': 'https://codecov.io/github/aio-libs/frozenlist',
        'Docs: RTD': 'https://frozenlist.readthedocs.io',
        'GitHub: issues': 'https://github.com/aio-libs/frozenlist/issues',
        'GitHub: repo': 'https://github.com/aio-libs/frozenlist',
    },
    license='Apache 2',
    packages=['frozenlist'],
    python_requires='>=3.5.3',
    install_requires=install_requires,
    include_package_data=True,
)

if not NO_EXTENSIONS:
    print("**********************")
    print("* Accellerated build *")
    print("**********************")
    setup(ext_modules=extensions,
          cmdclass=dict(build_ext=ve_build_ext),
          **args)
else:
    print("*********************")
    print("* Pure Python build *")
    print("*********************")
    setup(**args)
