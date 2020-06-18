# [ADR-0001] Standardize and automatize release flow

Status: **proposed**

Deciders: @redeboer @spflueger

Technical Story: Specification of [#68](https://github.com/ComPWA/expertsystem/issues/68)

## Context and Problem Statement

To create a release on PyPI, we currently tag a commit and Travis will automatically publish the package to PyPI. However, PyPI extracts the version number of the release from `setup.py`, not from the tag on GitHub. You therefore first have to create a PR that modifies `setup.py` and only then one can add tag it, see e.g. [#69](https://github.com/ComPWA/expertsystem/pull/69). This is not only bothersome, but also prone to errors.

*Note: this ADR also touches on our packaging system -- we currently only work with a `setup.py` file.*

## Considered Options

For an overview of common Python packaging techniques to maintain a single source of truth for the version number, see [here](https://packaging.python.org/guides/single-sourcing-package-version/).

* Option 1: [`[setuptools-scm]`](https://pypi.org/project/setuptools-scm/)
*

## Decision Outcome

Chosen option: Option 1, because [justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force force | … | comes out best (see below)].

### Positive Consequences <!-- optional -->

* [e.g., improvement of quality attribute satisfaction, follow-up decisions required, …]
* …

### Negative Consequences <!-- optional -->

* [e.g., compromising quality attribute, follow-up decisions required, …]
* …

## Pros and Cons of the Options <!-- optional -->

### [option 1]

[example | description | pointer to more information | …] <!-- optional -->

* Good, because [argument a]
* Good, because [argument b]
* Bad, because [argument c]
* … <!-- numbers of pros and cons can vary -->

### [option 2]

[example | description | pointer to more information | …] <!-- optional -->

* Good, because [argument a]
* Good, because [argument b]
* Bad, because [argument c]
* … <!-- numbers of pros and cons can vary -->

## Links <!-- optional -->

* [Link type] [Link to ADR] <!-- example: Refined by [ADR-0005](0005-example.md) -->
* … <!-- numbers of links can vary -->
