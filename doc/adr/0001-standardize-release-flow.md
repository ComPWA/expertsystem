# [ADR-0001] Standardize and automatize release flow

Status: **proposed**

Deciders: @redeboer @spflueger

Technical Story: Specification of [#68](https://github.com/ComPWA/expertsystem/issues/68)

## Context and Problem Statement

To create a release on PyPI, we currently tag a commit and Travis will automatically deploy the package to PyPI. However, PyPI extracts the version number from `setup.py`, not from the tag on GitHub. You therefore first have to create a PR that modifies `setup.py` and only then one can add tag it, see e.g. [#69](https://github.com/ComPWA/expertsystem/pull/69). This is not only bothersome, but also prone to errors.

Also, we currently use semantic version. Is this the best choice for this project?

*Note: this ADR also touches on our packaging system -- we currently only work with a `setup.py` file.*

## Considered Options

The following versioning schema were considered

* [semantic versioning](https://semver.org/)
* [romantic versioning](https://github.com/romversioning/romver)

Besides that, we considered the following packaging workflows.

* Option 1: [`pip`](https://pypi.org/project/pip/) +
            [`setuptools`](https://pypi.org/project/setuptools/) +
            [`setuptools-scm`](https://pypi.org/project/setuptools-scm/) +
            "manual" dependency pinning +
            [`twine`](https://pypi.org/project/twine/) +
            [`semantic versioning`](https://semver.org/)
* Option 2: [`poetry`](https://pypi.org/project/poetry/) +
            [`poetry-dynamic-versioning`](https://pypi.org/project/poetry-dynamic-versioning) +
            [`semantic versioning`](https://semver.org/)

For an overview of common Python packaging techniques to maintain a single source of truth for the version number, see [here](https://packaging.python.org/guides/single-sourcing-package-version/).

## Decision Outcome

Semantic versioning.

Chosen option: Option 1, because this seems to be most widely used. Note that the Python community seems not to have settled on a fixed solution, so we can just have to choose one option for now.


## Pros and Cons of the Options

### Option 1: `setuptools`

* Good, because current "standard" packaging tool
* Good, because current codebase is based on pip and setuptools
* Bad, dependency pinning and updating has to be done "manually"
  (pip freeze, etc)
* Bad, because requires several tools to publish a package

### Option 2: `poetry`

* Good, because single tool which provides all functionality to build and
  publish a package
* Good, because includes dependency pinning and update functionality
* Bad, because `poetry-dynamic-versioning` is a non stable package atm
* Bad, requires to switch from existing Option 1
* Bad, because quality & stability?
