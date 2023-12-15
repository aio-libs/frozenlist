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

1.4.1 (2023-12-15)
==================

Packaging updates and notes for downstreams
-------------------------------------------

- Declared Python 3.12 and PyPy 3.8-3.10 supported officially
  in the distribution package metadata.


  *Related issues and pull requests on GitHub:*
  :issue:`553`.

- Replaced the packaging is replaced from an old-fashioned :file:`setup.py` to an
  in-tree :pep:`517` build backend -- by :user:`webknjaz`.

  Whenever the end-users or downstream packagers need to build ``frozenlist``
  from source (a Git checkout or an sdist), they may pass a ``config_settings``
  flag ``pure-python``. If this flag is not set, a C-extension will be built
  and included into the distribution.

  Here is how this can be done with ``pip``:

  .. code-block:: console

      $ python3 -m pip install . --config-settings=pure-python=

  This will also work with ``-e | --editable``.

  The same can be achieved via ``pypa/build``:

  .. code-block:: console

      $ python3 -m build --config-setting=pure-python=

  Adding ``-w | --wheel`` can force ``pypa/build`` produce a wheel from source
  directly, as opposed to building an ``sdist`` and then building from it.


  *Related issues and pull requests on GitHub:*
  :issue:`560`.


Contributor-facing changes
--------------------------

- It is now possible to request line tracing in Cython builds using the
  ``with-cython-tracing`` :pep:`517` config setting
  -- :user:`webknjaz`.

  This can be used in CI and development environment to measure coverage
  on Cython modules, but is not normally useful to the end-users or
  downstream packagers.

  Here's a usage example:

  .. code-block:: console

      $ python3 -Im pip install . --config-settings=with-cython-tracing=true

  For editable installs, this setting is on by default. Otherwise, it's
  off unless requested explicitly.

  The following produces C-files required for the Cython coverage
  plugin to map the measurements back to the PYX-files:

  .. code-block:: console

      $ python -Im pip install -e .

  Alternatively, the ``FROZENLIST_CYTHON_TRACING=1`` environment variable
  can be set to do the same as the :pep:`517` config setting.


  *Related issues and pull requests on GitHub:*
  :issue:`560`.

- Coverage collection has been implemented for the Cython modules
  -- by :user:`webknjaz`.

  It will also be reported to Codecov from any non-release CI jobs.


  *Related issues and pull requests on GitHub:*
  :issue:`561`.

- A step-by-step :doc:`Release Guide <contributing/release_guide>` guide has
  been added, describing how to release *frozenlist* -- by :user:`webknjaz`.

  This is primarily targeting the maintainers.


  *Related issues and pull requests on GitHub:*
  :issue:`563`.

- Detailed :doc:`Contributing Guidelines <contributing/guidelines>` on
  authoring the changelog fragments have been published in the
  documentation -- by :user:`webknjaz`.


  *Related issues and pull requests on GitHub:*
  :issue:`564`.


----


1.4.0 (2023-07-12)
==================

The published source distribution package became buildable
under Python 3.12.


----


Bugfixes
--------

- Removed an unused :py:data:`typing.Tuple` import
  `#411 <https://github.com/aio-libs/frozenlist/issues/411>`_


Deprecations and Removals
-------------------------

- Dropped Python 3.7 support.
  `#413 <https://github.com/aio-libs/frozenlist/issues/413>`_


Misc
----

- `#410 <https://github.com/aio-libs/frozenlist/issues/410>`_, `#433 <https://github.com/aio-libs/frozenlist/issues/433>`_


----


1.3.3 (2022-11-08)
==================

- Fixed CI runs when creating a new release, where new towncrier versions
  fail when the current version section is already present.


----


1.3.2 (2022-11-08)
==================

Misc
----

- Updated the CI runs to better check for test results and to avoid deprecated syntax. `#327 <https://github.com/aio-libs/frozenlist/issues/327>`_


----


1.3.1 (2022-08-02)
==================

The published source distribution package became buildable
under Python 3.11.


----


1.3.0 (2022-01-18)
==================

Bugfixes
--------

- Do not install C sources with binary distributions.
  `#250 <https://github.com/aio-libs/frozenlist/issues/250>`_


Deprecations and Removals
-------------------------

- Dropped Python 3.6 support
  `#274 <https://github.com/aio-libs/frozenlist/issues/274>`_


----


1.2.0 (2021-10-16)
==================

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
