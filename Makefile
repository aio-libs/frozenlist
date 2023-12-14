# Some simple testing tasks (sorry, UNIX only).

PYXS = $(wildcard frozenlist/*.pyx)
SRC = frozenlist tests setup.py

all: test

.install-cython:
	pip install -r requirements/ci.txt
	touch .install-cython

frozenlist/%.c: frozenlist/%.pyx
	cython -3 -o $@ $< -I frozenlist

cythonize: .install-cython $(PYXS:.pyx=.c)

.install-deps: $(shell find requirements -type f)
	pip install -r requirements/ci.txt
ifndef CI
	pre-commit install
endif
	@touch .install-deps

lint: .install-deps
ifndef CI
	python -Im pre_commit run --all-files --show-diff-on-failure
else
	python -Im pre_commit run --all-files
endif

.develop: .install-deps $(shell find frozenlist -type f) lint
	pip install -e . --config-settings=pure-python=false
	@touch .develop

test: .develop
	@pytest -rxXs -q

vtest: .develop
	@pytest -rxXs -s -v

cov cover coverage:
	tox

cov-dev: .develop
	@pytest -rxXs --cov-report=html
	@echo "open file://`pwd`/htmlcov/index.html"

cov-ci-run: .develop
	@echo "Regular run"
	@pytest -rxXs --cov-report=html

cov-dev-full: cov-ci-run
	@echo "open file://`pwd`/htmlcov/index.html"

clean:
	@rm -rf `find . -name __pycache__`
	@rm -f `find . -type f -name '*.py[co]' `
	@rm -f `find . -type f -name '*~' `
	@rm -f `find . -type f -name '.*~' `
	@rm -f `find . -type f -name '@*' `
	@rm -f `find . -type f -name '#*#' `
	@rm -f `find . -type f -name '*.orig' `
	@rm -f `find . -type f -name '*.rej' `
	@rm -f .coverage
	@rm -rf htmlcov
	@rm -rf build
	@rm -rf cover
	@make -C docs clean
	@python setup.py clean
	@rm -f frozenlist/_frozenlist.html
	@rm -f frozenlist/_frozenlist.c
	@rm -f frozenlist/_frozenlist.*.so
	@rm -f frozenlist/_frozenlist.*.pyd
	@rm -rf .tox
	@rm -f .develop
	@rm -f .flake
	@rm -f .install-deps
	@rm -rf frozenlist.egg-info

doc:
	@make -C docs html SPHINXOPTS="-W --keep-going -n -E"
	@echo "open file://`pwd`/docs/_build/html/index.html"

doc-spelling:
	@make -C docs spelling SPHINXOPTS="-W --keep-going -n -E"

install:
	@pip install -U 'pip'
	@pip install -Ur requirements/dev.txt

install-dev: .develop

.PHONY: all build test vtest cov clean doc lint
