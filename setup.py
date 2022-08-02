import os
import sys

from setuptools import Extension, setup

NO_EXTENSIONS = (
    bool(os.environ.get("FROZENLIST_NO_EXTENSIONS"))
    or sys.implementation.name != "cpython"
)

if NO_EXTENSIONS:
    print("*********************")
    print("* Pure Python build *")
    print("*********************")
    ext_modules = None
else:
    print("*********************")
    print("* Accelerated build *")
    print("*********************")
    ext_modules = [Extension("frozenlist._frozenlist", ["frozenlist/_frozenlist.c"])]


setup(
    ext_modules=ext_modules,
)
