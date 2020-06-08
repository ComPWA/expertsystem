[![PyPI](https://badge.fury.io/py/expertsystem.svg)](https://pypi.org/project/expertsystem)
[![Travis CI](https://travis-ci.com/ComPWA/expertsystem.svg?branch=master)](https://travis-ci.com/ComPWA/expertsystem)
[![Test coverage](https://codecov.io/gh/ComPWA/expertsystem/branch/master/graph/badge.svg)](https://codecov.io/gh/ComPWA/expertsystem)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/db355758fb0e4654818b85997f03e3b8)](https://www.codacy.com/gh/ComPWA/expertsystem)
[![Documentation build status](https://readthedocs.org/projects/expertsystem/badge/?version=latest)](https://pwa.readthedocs.io/projects/expertsystem/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen)](https://github.com/pre-commit/pre-commit)

# PWA Expert System

The PWA Expert System is a tool for:

1. evaluating the validity of a particle reaction;
2. creating amplitude models that can be used by partial wave analysis
   frameworks.

As a user, you give the system an initial state and a final state, optionally
with certain rules you want to apply. The expert system then constructs several
hypotheses for what happens during the transition from initial to final state.

## How it works

The expert system works with **state transition graphs** that represent the
allowed transitions from an initial state to a final state. A state transition
graph consists of **nodes** and **edges** (in correspondence to Feynman
graphs):

- We call the connection lines **particle lines**. These are basically a list
  of quantum numbers (QN) that define the particle state. (This list can be
  empty at first).
- The nodes are of type `InteractionNode` and contain all information for the
  transition of this specific step. An interaction node has 𝑀 ingoing lines
  and 𝑁 outgoing lines (𝑀, 𝑁 ∈ 𝕫, 𝑀 > 0, 𝑁 > 0).

## Workflow for building a graph

### Step 1

Building of all possible topologies. A **topology** is a graph, in which the
edges and nodes are empty (no QN information). See the topology sub-modules.

### Step 2

Filling the topology graphs with QN information. This means initializing the
topology graphs with the initial and final state QNs and *propagating* these
numbers through the complete graph. Here, the combinatorics of the initial and
final state should also be taken into account.

### Step 3

Duplicate the graphs and insert concrete particles for the edges (inserting the
mass variable).

### Step 4

Write output to XML model file.

## Design and available features

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
- [ ] **I/O**: Write transition graph to human-readable recipe file
  - [x] XML (*old ComPWA format*)
  - [ ] YAML
