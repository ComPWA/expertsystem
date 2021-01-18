<!-- markdownlint-disable MD013 -->
<!-- cspell:ignore lambdify -->

# [ADR-001] Amplitude model

- Status: **accepted**
- Deciders: @redeboer @spflueger

## Context and Problem Statement

From the perspective of a PWA fitter package, the responsibility of the
`expertsystem` is to construct an `AmplitudeModel` that can serve as a template
for a function that is to be fitted to a dataset. Such a **function** has the
following requirements:

1. It should be able to compute a list of real-valued intensities
   $\mathbb{R}^m$ from a dataset of four-momenta
   $\mathbb{R}^{m\times n\times4}$, where $m$ is the number of events and $n$
   is the number of final state particles.
2. It should contain **parameters** that can be tweaked, so that they can be
   optimized with regard to a certain estimator.

Currently
([v0.6.9](https://pwa.readthedocs.io/projects/expertsystem/en/0.6.8)), the
[`AmplitudeModel`](https://pwa.readthedocs.io/projects/expertsystem/en/0.6.8/api/expertsystem.amplitude.model.html#expertsystem.amplitude.model.AmplitudeModel)
contains five **sections** (instances of specific classes):

- `kinematics`: defines initial and final state
- `particles`: particle definitions (spin, etc.)
- `dynamics`: a mapping that defines which dynamics type to apply to which
  particle
- `intensity`: the actual amplitude model that is to be converted by a fitter
  package into a function as described above
- `parameters`: an inventory of parameters that are used in `intensity` and
  `dynamics`

This structure can be represented in YAML, see an example
[here](https://github.com/ComPWA/expertsystem/blob/f4f1c55/tests/unit/io/expected_recipe.yml).

A fitter package converts `intensity` together with `dynamics` into a function.
Any references to parameters that `intensity` or `dynamics` contain are
converted into a parameter of the function. The parameters are initialized with
the value as listed in the `parameters` section of the `AmplitudeModel`.

## Decision Drivers

- [#382](https://github.com/ComPWA/expertsystem/issues/382): Coupling
  parameters in the `AmplitudeModel` is difficult (has to be done through the
  place where they are used in the `dynamics` or `intensity` section) and
  counter-intuitive (cannot be done through the `parameters` section)
- [#440](https://github.com/ComPWA/expertsystem/issues/440): when overwriting
  existing dynamics, old parameters are not cleaned up from the `parameters`
  section
- [#441](https://github.com/ComPWA/expertsystem/issues/441): parameters contain
  a name that can be changed, but that results in a mismatch between the key
  that is used in the `parameters` section and the name of the parameter to
  which that entry points.

## Considered Options

```{toctree}
---
maxdepth: 1
---
examples/001/sympy
examples/001/operators
```

## Decision Outcome

Use {doc}`examples/001/sympy`.

## Pros and Cons of the Options

### {doc}`SymPy <examples/001/sympy>`

- **Positive**
  - Easy to render amplitude model as LaTeX
  - Use
    [`lambdify`](https://docs.sympy.org/latest/tutorial/basic_operations.html#lambdify)
    to convert the expression to any back-end
  - Use `Expr.subs` (substitute) to couple parameters or replace components of
    the model, for instance to set custom dynamics
- **Negative**
  - Need to keep track of components in the expression tree with symbol
    mappings

### {doc}`Python's operator library <examples/001/operators>`

- **Positive**
  - More control over different components of in the expression tree
- **Negative**
  - Essentially re-inventing SymPy
