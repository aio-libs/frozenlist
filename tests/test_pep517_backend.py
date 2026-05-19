"""Tests for the in-tree PEP 517 build backend.

These exercise the bits of ``packaging/pep517_backend/`` that drive the
reproducibility behaviour added for issue #577: the ``build-inplace``
config-setting / ``FROZENLIST_BUILD_INPLACE`` env-var precedence ladder, and
the ``-ffile-prefix-map`` injection into ``CFLAGS`` / ``CXXFLAGS`` from
``patched_env``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_BACKEND_PARENT = _REPO_ROOT / "packaging"
if str(_BACKEND_PARENT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_PARENT))

from pep517_backend._backend import (  # noqa: E402
    BUILD_INPLACE_CONFIG_SETTING,
    BUILD_INPLACE_ENV_VAR,
    _build_inplace,
)
from pep517_backend._cython_configuration import patched_env  # noqa: E402


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Strip env vars that could leak into the build-inplace lookup."""
    monkeypatch.delenv(BUILD_INPLACE_ENV_VAR, raising=False)
    monkeypatch.delenv("CFLAGS", raising=False)
    monkeypatch.delenv("CXXFLAGS", raising=False)


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
        assert expected in os.environ["CFLAGS"].split()
        assert expected in os.environ["CXXFLAGS"].split()


def test_patched_env_skipped_when_no_tmp_dir(
    clean_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "platform", "linux")

    with patched_env(
        env={},
        cython_line_tracing_requested=False,
    ):
        assert "CFLAGS" not in os.environ
        assert "CXXFLAGS" not in os.environ


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
        assert "CFLAGS" not in os.environ
        assert "CXXFLAGS" not in os.environ


def test_patched_env_line_tracing_still_applied_on_windows(
    clean_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "platform", "win32")

    with patched_env(
        env={},
        cython_line_tracing_requested=True,
    ):
        assert "-DCYTHON_TRACE_NOGIL=1" in os.environ["CFLAGS"].split()
        assert "-DCYTHON_TRACE_NOGIL=1" in os.environ["CXXFLAGS"].split()


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
            pass


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
    src_dir = tmp_path / src_name
    build_dir = tmp_path / build_name
    with pytest.raises(ValueError, match="whitespace"):
        with patched_env(
            env={},
            cython_line_tracing_requested=False,
            original_source_directory=src_dir,
            temporary_build_directory=build_dir,
        ):
            pass


def test_patched_env_appends_to_existing_cflags(
    clean_env: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("CFLAGS", "-O2")
    monkeypatch.setenv("CXXFLAGS", "-O3")
    src_dir = tmp_path / "src"
    build_dir = tmp_path / "build"
    src_dir.mkdir()
    build_dir.mkdir()

    with patched_env(
        env={},
        cython_line_tracing_requested=False,
        original_source_directory=src_dir,
        temporary_build_directory=build_dir,
    ):
        assert "-O2" in os.environ["CFLAGS"].split()
        assert "-O3" in os.environ["CXXFLAGS"].split()
        assert any(
            tok.startswith("-ffile-prefix-map=") for tok in os.environ["CFLAGS"].split()
        )
