"""Tests for the in-tree PEP 517 build backend.

These exercise the bits of ``packaging/pep517_backend/`` that drive the
reproducibility behaviour added for issue #577: the ``build-inplace``
config-setting / ``FROZENLIST_BUILD_INPLACE`` env-var precedence ladder, the
``-ffile-prefix-map`` injection into ``CFLAGS`` / ``CXXFLAGS`` from
``patched_env``, and the way ``maybe_prebuild_c_extensions`` /
``build_editable`` thread those paths through to the Cython env hook.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

# The build backend transitively imports ``expandvars``, which is a build-time
# dependency declared in ``pyproject.toml`` rather than a test requirement. CI
# only installs it on the non-``no-extensions`` matrix cells where the wheel
# is built; on the ``FROZENLIST_NO_EXTENSIONS=Y`` cells it is absent, so skip
# this module there instead of failing to collect.
pytest.importorskip("expandvars")

# ``sys.path`` is amended in ``conftest.py`` so the in-tree PEP 517 backend
# under ``packaging/`` becomes importable.
from pep517_backend import _backend  # noqa: E402
from pep517_backend._backend import (  # noqa: E402
    BUILD_INPLACE_CONFIG_SETTING,
    BUILD_INPLACE_ENV_VAR,
    _build_inplace,
    build_editable,
    maybe_prebuild_c_extensions,
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


def _install_backend_stubs(
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, object]:
    """Replace the heavy bits of the build pipeline with cheap recorders.

    Returns a dict the caller can inspect to assert on observed arguments.
    Used by ``maybe_prebuild_c_extensions`` / ``build_editable`` tests so the
    contexts can be entered without invoking ``cythonize`` or ``setuptools``.
    """
    observed: dict[str, object] = {}

    def fake_get_config() -> dict[str, object]:
        return {"env": {}, "flags": {}, "kwargs": {}, "src": []}

    def fake_make_args(config: object, line_tracing: bool) -> list[str]:
        return []

    def fake_cythonize(args: list[str]) -> None:
        observed["cythonize_called"] = True

    def fake_build_editable(
        wheel_directory: str,
        config_settings: object = None,
        metadata_directory: str | None = None,
    ) -> str:
        observed["editable_directory"] = wheel_directory
        return "stub-editable"

    @contextmanager
    def fake_patched_env(
        env: dict[str, str],
        cython_line_tracing_requested: bool,
        *,
        original_source_directory: Path | None = None,
        temporary_build_directory: Path | None = None,
    ) -> Iterator[None]:
        observed["original_source_directory"] = original_source_directory
        observed["temporary_build_directory"] = temporary_build_directory
        yield

    monkeypatch.setattr(_backend, "_get_local_cython_config", fake_get_config)
    monkeypatch.setattr(
        _backend,
        "_make_cythonize_cli_args_from_config",
        fake_make_args,
    )
    monkeypatch.setattr(_backend, "_cythonize_cli_cmd", fake_cythonize)
    monkeypatch.setattr(_backend, "_setuptools_build_editable", fake_build_editable)
    monkeypatch.setattr(_backend, "_patched_cython_env", fake_patched_env)
    return observed


def test_maybe_prebuild_c_extensions_inplace_passes_no_tmp_dir(
    clean_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``build_inplace=True`` takes the ``nullcontext`` branch.

    ``patched_env`` should receive ``temporary_build_directory=None`` so the
    ``-ffile-prefix-map`` flag is *not* injected when the build runs in-tree.
    """
    observed = _install_backend_stubs(monkeypatch)

    with maybe_prebuild_c_extensions(build_inplace=True):
        pass

    assert observed["temporary_build_directory"] is None
    assert isinstance(observed["original_source_directory"], Path)
    assert observed["cythonize_called"] is True


def test_maybe_prebuild_c_extensions_tmp_dir_threads_paths(
    clean_env: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """``build_inplace=False`` enters ``_in_temporary_directory``.

    Verify both ``original_source_directory`` and ``temporary_build_directory``
    are forwarded to ``patched_env`` so the reproducibility flag fires.
    """
    observed = _install_backend_stubs(monkeypatch)
    fake_tmp_dir = tmp_path / "fake-tmp"
    fake_tmp_dir.mkdir()

    @contextmanager
    def fake_in_temporary_directory(src_dir: Path) -> Iterator[Path]:
        observed["in_tmp_src_dir"] = src_dir
        yield fake_tmp_dir

    monkeypatch.setattr(
        _backend,
        "_in_temporary_directory",
        fake_in_temporary_directory,
    )

    with maybe_prebuild_c_extensions(build_inplace=False):
        pass

    assert observed["temporary_build_directory"] == fake_tmp_dir
    assert observed["original_source_directory"] == observed["in_tmp_src_dir"]


def test_build_editable_warns_when_user_disables_inplace(
    clean_env: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """``build_editable`` rejects ``build-inplace=false`` with a warning.

    Editable installs require in-tree artifacts; downstream packagers passing
    the opt-out get a ``RuntimeWarning`` explaining why their override was
    ignored. Covers the ``build_editable`` warning branch.
    """
    _install_backend_stubs(monkeypatch)

    with pytest.warns(RuntimeWarning, match="in-tree"):
        result = build_editable(
            str(tmp_path),
            config_settings={BUILD_INPLACE_CONFIG_SETTING: "false"},
        )
    assert result == "stub-editable"
