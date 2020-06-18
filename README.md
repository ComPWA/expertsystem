[![PyPI](https://badge.fury.io/py/expertsystem.svg)](https://pypi.org/project/expertsystem)
[![Travis CI](https://travis-ci.com/ComPWA/expertsystem.svg?branch=master)](https://travis-ci.com/ComPWA/expertsystem)
[![Test coverage](https://codecov.io/gh/ComPWA/expertsystem/branch/master/graph/badge.svg)](https://codecov.io/gh/ComPWA/expertsystem)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/db355758fb0e4654818b85997f03e3b8)](https://www.codacy.com/gh/ComPWA/expertsystem)
[![Documentation build status](https://readthedocs.org/projects/expertsystem/badge/?version=latest)](https://pwa.readthedocs.io/projects/expertsystem/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen)](https://github.com/pre-commit/pre-commit)

# PWA Expert System

## About

The two purposes of the Partial Wave Analysis Expert System are to:

1. validate a particle reaction, based on given information. E.g.: Can a 𝜋⁰
   decay into 1, 2, 3 𝛾 particles?
2. create partial wave analysis amplitude models, based on basic information of
   a reaction. E.g.: Create an amplitude for J/𝜓 → 𝛾𝜋⁰𝜋⁰ in the helicity or
   canonical formalism.

The user only has to provide a basic information of the particle reaction, such
as an initial state and a final state. Helper functions provide easy ways to
configure the system, but the user still has full control. The expert system
then constructs several hypotheses for what happens during the transition from
initial to final state. Read more on this in the [Design section](#Design).

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

## Design

Internally, the PWA Expert System consists of three major components.

### 1. State Transition Graphs
A `StateTransitionGraph` is a [directed
graph](https://en.wikipedia.org/wiki/Directed_graph) that consists of **nodes**
and **edges**. In a directed graph, each edge must be connected to at least one
node (in correspondence to Feynman graphs). This way, a graph describes the
transition from one state to another.

- The edges correspond to particles/states, in other words a collection of
  properties such as the quantum numbers that characterize the particle state.

- Each node represents an interaction and contains all information for the
  transition of this specific step. Most importantly, a node contains a
  collection of conservation rules that have to be satisfied. An interaction
  node has 𝑀 ingoing lines and 𝑁 outgoing lines, where 𝑀, 𝑁 ∈ 𝕫, 𝑀 > 0, 𝑁 > 0.

### 2. Conservation Rules
The central component of the expert system are the conservation rules. They
belong to individual nodes and receive properties about the node itself, as
well as properties of the ingoing and outgoing edges of that node. Based on
those properties the conservation rules determine whether edges pass or not.

### 3. Solvers
The propagation of the correct state properties through the graph is done by
solvers. New properties are set for intermediate edges and interaction nodes
and their validity is checked with the conservation rules.

## Workflow of the Expert System

1. Preparation

   1.1. Build all possible topologies. A **topology** is represented by a
   [graph](#State-Transition-Graphs), in which the edges and nodes are empty
   (no particle information).

   1.2. Fill the topology graphs with the user provided information. Typically
   these are the graph's ingoing edges (initial state) and outgoing edges
   (final state).

2. Solving

   2.1. *Propagate* quantum number information through the complete graph while
   respecting the specified conservation laws. Information like mass is not
   used in this first solving step.

   2.2. *Clone* graphs while inserting concrete matching particles for the
   intermediate edges (mainly adds the mass variable).

   2.3. *Validate* the complete graphs, so run all conservation law check that
   were postponed from the first step.

3. Generate an amplitude model, e.g. helicity or canonical amplitude.

## Usage

Check out the Jupyter notebooks on the [Usage
page](https://pwa.readthedocs.io/projects/expertsystem/en/latest/usage.html) of
the expertsystem!
