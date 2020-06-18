[![PyPI](https://badge.fury.io/py/expertsystem.svg)](https://pypi.org/project/expertsystem)
[![Travis CI](https://travis-ci.com/ComPWA/expertsystem.svg?branch=master)](https://travis-ci.com/ComPWA/expertsystem)
[![Test coverage](https://codecov.io/gh/ComPWA/expertsystem/branch/master/graph/badge.svg)](https://codecov.io/gh/ComPWA/expertsystem)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/db355758fb0e4654818b85997f03e3b8)](https://www.codacy.com/gh/ComPWA/expertsystem)
[![Documentation build status](https://readthedocs.org/projects/expertsystem/badge/?version=latest)](https://pwa.readthedocs.io/projects/expertsystem/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen)](https://github.com/pre-commit/pre-commit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# PWA Expert System

Visit
[expertsystem.rtfd.io](https://pwa.readthedocs.io/projects/expertsystem/en/latest/)
for an introduction to the Particle Wave Analysis Expert System!

## Available features

- [ ] **Input**: Particle database
  - [ ] Source of truth: PDG
  - [x] Option to overwrite and append with custom particle definitions
- [ ] **State transition graph**
  - [ ] ...
- [ ] **Conservation rules**
  - [ ] Easily extendable
    - [ ] User input
    - [ ] Open-closed design
  - [ ] ...
- [ ] **Generate amplitude models for PWA formalisms**
  - [x] Helicity formalism
  - [x] Canonical formalism
  - [ ] Spin projection formalisms
  - [ ] Tensor formalisms
- [ ] **I/O**: Write transition graph to human-readable recipe file
  - [x] XML (*old format for [ComPWA](https://compwa.github.io/)*)
  - [ ] YAML (*new format for
    [tensorwaves](https://pwa.readthedocs.io/projects/tensorwaves/en/latest)*)
