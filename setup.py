import os
import pathlib
import re
import sys

from setuptools import Extension, setup

try:
    from Cython.Build import cythonize
    CYTHON = True
except ImportError:
    CYTHON = False


if sys.version_info < (3, 5, 3):
    raise RuntimeError("frozenlist 1.x requires Python 3.5.3+")


NO_EXTENSIONS = (
    bool(os.environ.get('FROZENLIST_NO_EXTENSIONS')) or
    sys.implementation.name != "cpython"
)

here = pathlib.Path(__file__).parent

if CYTHON:
    # convert .pyx files to .c files
    # this happens for pure-python builds too because
    # we'd want to be able to include the .c file
    # in source distributions.
    modules = cythonize('frozenlist/_frozenlist.pyx')
else:
    # No Cython, fall back to a distributed .c source
    # file, if available.
    c_source = here / 'frozenlist' / '_frozenlist.c'
    if c_source.exists():
        modules = [
            Extension('frozenlist._frozenlist', [str(c_source)])
        ]
    else:
        if not NO_EXTENSIONS:
            print(
                "Cython not available to produce .c file\n"
                "Falling back to pure Python build.\n"
            )
        NO_EXTENSIONS = True

if NO_EXTENSIONS:
    print("*********************")
    print("* Pure Python build *")
    print("*********************")
    ext_modules = None

else:
    ext_modules = modules

txt = (here / 'frozenlist' / '__init__.py').read_text('utf-8')
try:
    version = re.findall(r"^__version__ = '([^']+)'\r?$",
                         txt, re.M)[0]
except IndexError:
    raise RuntimeError('Unable to determine version.')

install_requires = []


def read(f):
    return (here / f).read_text('utf-8').strip()


setup(
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
        'CI: Azure Pipelines':
            'https://dev.azure.com/aio-libs/frozenlib/_build',
        'Coverage: codecov': 'https://codecov.io/github/aio-libs/frozenlist',
        'Docs: RTD': 'https://frozenlist.readthedocs.io',
        'GitHub: issues': 'https://github.com/aio-libs/frozenlist/issues',
        'GitHub: repo': 'https://github.com/aio-libs/frozenlist',
    },
    license='Apache 2',
    packages=['frozenlist'],
    ext_modules=ext_modules,
    python_requires='>=3.5.3',
    install_requires=install_requires,
    include_package_data=True,
)
