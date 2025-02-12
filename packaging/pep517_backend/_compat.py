"""Cross-python stdlib shims."""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

try:
    from contextlib import chdir as chdir_cm
except ImportError:

    @contextmanager  # type: ignore[no-redef]
    def chdir_cm(path: os.PathLike[str]) -> Iterator[None]:
        """Temporarily change the current directory, recovering on exit."""
        original_wd = Path.cwd()
        os.chdir(path)
        try:
            yield
        finally:
            os.chdir(original_wd)


try:
    from tomllib import loads as load_toml_from_string
except ImportError:
    from tomli import loads as load_toml_from_string


__all__ = ("chdir_cm", "load_toml_from_string")  # noqa: WPS410
