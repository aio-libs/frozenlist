"""Tests for the in-tree PEP 517 build backend."""

import os
import shlex
import sys
import sysconfig

import pytest
from pep517_backend._cython_configuration import patched_env
from setuptools._distutils.ccompiler import new_compiler
from setuptools._distutils.sysconfig import customize_compiler

TRACE_MACRO = "-DCYTHON_TRACE_NOGIL=1"


def _interpreter_flags() -> list[str]:
    """Return the compiler flags CPython was configured with."""
    cflags: str = sysconfig.get_config_var("CFLAGS") or ""
    return shlex.split(cflags)


def _configured_compile_command() -> list[str]:
    """Return the compile command setuptools derives from the environment."""
    compiler = new_compiler()
    customize_compiler(compiler)
    # ``customize_compiler`` sets this attribute dynamically.
    command: list[str] = compiler.compiler_so  # type: ignore[attr-defined]
    return command


@pytest.mark.parametrize("tracing", [True, False])
def test_tracing_macro_goes_through_cppflags(
    monkeypatch: pytest.MonkeyPatch, tracing: bool
) -> None:
    """The macro is appended to CPPFLAGS and CFLAGS is left alone.

    A CFLAGS environment variable replaces the interpreter's own compiler
    flags in setuptools' distutils, which silently drops -O3 from the
    build, while CPPFLAGS is appended to them.
    """
    monkeypatch.setenv("CFLAGS", "-fuser-cflag")
    monkeypatch.setenv("CPPFLAGS", "-DUSER=1")

    with patched_env({}, tracing):
        cppflags = shlex.split(os.environ["CPPFLAGS"])
        assert os.environ["CFLAGS"] == "-fuser-cflag"

    assert cppflags[0] == "-DUSER=1"
    assert (TRACE_MACRO in cppflags) is tracing
    assert os.environ["CPPFLAGS"] == "-DUSER=1"


@pytest.mark.skipif(
    sys.platform == "win32", reason="MSVC does not read CFLAGS or CPPFLAGS"
)
def test_interpreter_flags_survive_the_build_env() -> None:
    """The compiler still gets the interpreter's flags plus the macro.

    This drives setuptools' real compiler customization, so it fails if the
    backend ever goes back to setting CFLAGS.
    """
    with patched_env({}, True):
        command = _configured_compile_command()

    for flag in _interpreter_flags():
        assert flag in command
    assert TRACE_MACRO in command
