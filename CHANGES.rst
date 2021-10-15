=========
Changelog
=========

..
    You should *NOT* be adding new change log entries to this file, this
    file is managed by towncrier. You *may* edit previous change logs to
    fix problems like typo corrections or such.
    To add a new change log entry, please see
    https://pip.pypa.io/en/latest/development/contributing/#news-entries
    we named the news folder "changes".

    WARNING: Don't drop the next directive!

.. towncrier release notes start

1.2.0a8 (2021-10-15)
====================

Features
--------

- ``FrozenList`` now supports being used as a generic type as per PEP 585, e.g. ``frozen_int_list: FrozenList[int]`` (requires Python 3.9 or newer).
  `#172 <https://github.com/aio-libs/frozenlist/issues/172>`_
- Added support for Python 3.10.
  `#227 <https://github.com/aio-libs/frozenlist/issues/227>`_
- Started shipping platform-specific wheels with the ``musl`` tag targeting typical Alpine Linux runtimes.
  `#227 <https://github.com/aio-libs/frozenlist/issues/227>`_
- Started shipping platform-specific arm64 wheels for Apple Silicon.
  `#227 <https://github.com/aio-libs/frozenlist/issues/227>`_


----


1.1.1 (2020-11-14)
==================

Bugfixes
--------

- Provide x86 Windows wheels.
  `#169 <https://github.com/aio-libs/frozenlist/issues/169>`_


----


1.1.0 (2020-10-13)
==================

Features
--------

- Add support for hashing of a frozen list.
  `#136 <https://github.com/aio-libs/frozenlist/issues/136>`_

- Support Python 3.8 and 3.9.

- Provide wheels for ``aarch64``, ``i686``, ``ppc64le``, ``s390x`` architectures on
  Linux as well as ``x86_64``.


----


1.0.0 (2019-11-09)
==================

Deprecations and Removals
-------------------------

- Dropped support for Python 3.5; only 3.6, 3.7 and 3.8 are supported going forward.
  `#24 <https://github.com/aio-libs/frozenlist/issues/24>`_
