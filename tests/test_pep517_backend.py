"""Tests for the in-tree PEP 517 build backend."""

import os
import shlex
import sys
import sysconfig
from pathlib import Path

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


@pytest.mark.parametrize(
    ("platform", "expects_prefix_map"),
    [("linux", True), ("darwin", True), ("win32", False)],
)
def test_extra_flags_go_through_cppflags(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    platform: str,
    expects_prefix_map: bool,
) -> None:
    """Extra flags are appended to CPPFLAGS and CFLAGS is left alone.

    A CFLAGS environment variable replaces the interpreter's own compiler
    flags in setuptools' distutils, which silently drops -O3 from the
    build, while CPPFLAGS is appended to them.
    """
    monkeypatch.setattr(sys, "platform", platform)
    monkeypatch.setenv("CFLAGS", "-fuser-cflag")
    monkeypatch.setenv("CPPFLAGS", "-DUSER=1")
    source_dir = tmp_path / "src"
    build_dir = tmp_path / "build"
    prefix_map = f"-ffile-prefix-map={build_dir}={source_dir}"

    with patched_env(
        {},
        True,
        original_source_directory=source_dir,
        temporary_build_directory=build_dir,
    ):
        cppflags = os.environ["CPPFLAGS"].split(" ")
        assert os.environ["CFLAGS"] == "-fuser-cflag"

    assert cppflags[0] == "-DUSER=1"
    assert TRACE_MACRO in cppflags
    assert (prefix_map in cppflags) is expects_prefix_map
    assert os.environ["CPPFLAGS"] == "-DUSER=1"


@pytest.mark.parametrize("tracing", [True, False])
def test_tracing_macro_follows_the_request(
    monkeypatch: pytest.MonkeyPatch, tracing: bool
) -> None:
    """The line tracing macro is defined only when tracing is requested."""
    monkeypatch.delenv("CPPFLAGS", raising=False)

    with patched_env({}, tracing):
        cppflags = os.environ.get("CPPFLAGS", "").split(" ")

    assert (TRACE_MACRO in cppflags) is tracing


@pytest.mark.skipif(
    sys.platform == "win32", reason="MSVC does not read CFLAGS or CPPFLAGS"
)
def test_interpreter_flags_survive_the_build_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The compiler still gets the interpreter's flags plus the extra ones.

    This drives setuptools' real compiler customization, so it fails if the
    backend ever goes back to setting CFLAGS.
    """
    # A developer shell exporting these would replace the flags up front.
    monkeypatch.delenv("CFLAGS", raising=False)
    monkeypatch.delenv("CPPFLAGS", raising=False)
    source_dir = tmp_path / "src"
    build_dir = tmp_path / "build"

    with patched_env(
        {},
        True,
        original_source_directory=source_dir,
        temporary_build_directory=build_dir,
    ):
        command = _configured_compile_command()

    for flag in _interpreter_flags():
        assert flag in command
    assert TRACE_MACRO in command
    assert f"-ffile-prefix-map={build_dir}={source_dir}" in command
