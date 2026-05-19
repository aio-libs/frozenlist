"""Tests for the in-tree PEP 517 build backend."""

import os
import shlex
import sys
import sysconfig
from pathlib import Path

import pytest
from pep517_backend._backend import (
    BUILD_INPLACE_CONFIG_SETTING,
    BUILD_INPLACE_ENV_VAR,
    _build_inplace,
)
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
        cppflags = os.environ["CPPFLAGS"].split(" ")
        assert os.environ["CFLAGS"] == "-fuser-cflag"

    assert cppflags[0] == "-DUSER=1"
    assert (TRACE_MACRO in cppflags) is tracing
    assert os.environ["CPPFLAGS"] == "-DUSER=1"


@pytest.mark.skipif(
    sys.platform == "win32", reason="MSVC does not read CFLAGS or CPPFLAGS"
)
def test_interpreter_flags_survive_the_build_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The compiler still gets the interpreter's flags plus the macro.

    This drives setuptools' real compiler customization, so it fails if the
    backend ever goes back to setting CFLAGS.
    """
    # A developer shell exporting these would replace the flags up front.
    monkeypatch.delenv("CFLAGS", raising=False)
    monkeypatch.delenv("CPPFLAGS", raising=False)

    with patched_env({}, True):
        command = _configured_compile_command()

    for flag in _interpreter_flags():
        assert flag in command
    assert TRACE_MACRO in command


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Strip env vars that could leak into the build-inplace lookup."""
    monkeypatch.delenv(BUILD_INPLACE_ENV_VAR, raising=False)
    monkeypatch.delenv("CPPFLAGS", raising=False)


def test_build_inplace_default_false(clean_env: None) -> None:
    assert _build_inplace() is False


def test_build_inplace_default_true(clean_env: None) -> None:
    assert _build_inplace(default=True) is True


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("true", True),
        ("1", True),
        ("on", True),
        ("", True),
        ("false", False),
        ("0", False),
        ("off", False),
    ],
)
def test_build_inplace_config_setting(
    clean_env: None,
    value: str,
    expected: bool,
) -> None:
    assert (
        _build_inplace(
            {BUILD_INPLACE_CONFIG_SETTING: value},
        )
        is expected
    )


def test_build_inplace_env_var(
    clean_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(BUILD_INPLACE_ENV_VAR, "true")
    assert _build_inplace() is True


def test_build_inplace_config_setting_beats_env_var(
    clean_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(BUILD_INPLACE_ENV_VAR, "true")
    assert (
        _build_inplace(
            {BUILD_INPLACE_CONFIG_SETTING: "false"},
        )
        is False
    )


def test_patched_env_injects_flag_when_tmp_dir_set(
    clean_env: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    src_dir = tmp_path / "src"
    build_dir = tmp_path / "build"
    src_dir.mkdir()
    build_dir.mkdir()
    expected = f"-ffile-prefix-map={build_dir!s}={src_dir!s}"

    with patched_env(
        env={},
        cython_line_tracing_requested=False,
        original_source_directory=src_dir,
        temporary_build_directory=build_dir,
    ):
        assert expected in os.environ["CPPFLAGS"].split()


def test_patched_env_skipped_when_no_tmp_dir(
    clean_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "platform", "linux")

    with patched_env(
        env={},
        cython_line_tracing_requested=False,
    ):
        assert "CPPFLAGS" not in os.environ


def test_patched_env_skipped_on_windows(
    clean_env: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(sys, "platform", "win32")

    with patched_env(
        env={},
        cython_line_tracing_requested=False,
        original_source_directory=tmp_path / "src",
        temporary_build_directory=tmp_path / "build",
    ):
        assert "CPPFLAGS" not in os.environ


def test_patched_env_line_tracing_still_applied_on_windows(
    clean_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "platform", "win32")

    with patched_env(
        env={},
        cython_line_tracing_requested=True,
    ):
        assert TRACE_MACRO in os.environ["CPPFLAGS"].split()


def test_patched_env_raises_when_source_dir_missing(
    clean_env: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    with pytest.raises(ValueError, match="original_source_directory"):
        with patched_env(
            env={},
            cython_line_tracing_requested=False,
            original_source_directory=None,
            temporary_build_directory=tmp_path / "build",
        ):
            pass  # pragma: no cover


@pytest.mark.parametrize(
    ("src_name", "build_name"),
    [
        ("src with space", "build"),
        ("src", "build with space"),
    ],
)
def test_patched_env_raises_on_whitespace_in_paths(
    clean_env: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    src_name: str,
    build_name: str,
) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    with pytest.raises(ValueError, match="whitespace"):
        with patched_env(
            env={},
            cython_line_tracing_requested=False,
            original_source_directory=tmp_path / src_name,
            temporary_build_directory=tmp_path / build_name,
        ):
            pass  # pragma: no cover


def test_patched_env_appends_to_existing_cppflags(
    clean_env: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("CPPFLAGS", "-DUSER=1")
    monkeypatch.setenv("CFLAGS", "-fuser-cflag")

    with patched_env(
        env={},
        cython_line_tracing_requested=False,
        original_source_directory=tmp_path / "src",
        temporary_build_directory=tmp_path / "build",
    ):
        cppflags = os.environ["CPPFLAGS"].split()
        assert cppflags[0] == "-DUSER=1"
        assert cppflags[1].startswith("-ffile-prefix-map=")
        assert os.environ["CFLAGS"] == "-fuser-cflag"
