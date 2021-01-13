<!-- markdownlint-disable MD013 -->
<!-- cspell:ignore elif getattr isinstance literalinclude setattr staticmethod -->

# [ADR-0001] How to handle model parameters

- Status: **proposed**
- Deciders: @redeboer @spflueger

## Context and Problem Statement

From the perspective of a PWA fitter package, the responsibility of the
`expertsystem` is to construct an `AmplitudeModel` that can serve as a template
for a function that is to be fitted to a dataset. Such a **function** has the
following requirements:

1. It should be able to compute a list of real-valued intensities 𝐯𝐞𝐜⟨ℝ⟩(𝑚)
   from a dataset of four-momenta 𝐯𝐞𝐜<ℝⁿ⁴>(𝑚). Here, 𝑚 is the number of events
   and 𝑛 is the number of final state particles.
2. It should contain **parameters** that can be tweaked, so that they can be
   optimized with regard to a certain estimator.

Currently
([v0.6.7](https://pwa.readthedocs.io/projects/expertsystem/en/0.6.7)), the
[`AmplitudeModel`](https://pwa.readthedocs.io/projects/expertsystem/en/0.6.7/api/expertsystem.amplitude.model.html#expertsystem.amplitude.model.AmplitudeModel)
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

````{dropdown} Option 0: WIP
```{literalinclude} ./examples/0001/prototype.py

```
````

````{dropdown} Option 1: parameter _container_
Remove `name` from the `FitParameter` class and give the `FitParameters`
collection class the responsibility to keep track of 'names' of the
`FitParameter`s as keys in a `dict`. In the `AmplitudeModel`, locations where a
`FitParameter` should be inserted are indicated by an immutable (!) `str` that
should exist as a key in the `FitParameters`.

Such a setup best reflects the structure of the `AmplitudeModel` that we have
now (best illustrated by
[`expected_recipe`](https://github.com/ComPWA/expertsystem/blob/f4f1c553780e263eb5b2a478951223694386f22a/tests/unit/io/expected_recipe.yml),
note in particular YAML anchors like
[`&par1`](https://github.com/ComPWA/expertsystem/blob/f4f1c553780e263eb5b2a478951223694386f22a/tests/unit/io/expected_recipe.yml#L11)/[`*par1`](https://github.com/ComPWA/expertsystem/blob/f4f1c553780e263eb5b2a478951223694386f22a/tests/unit/io/expected_recipe.yml#L59)).
It also allows one to couple `FitParameters`. See following snippet:

```{literalinclude} ./examples/0001/parameter_container.py

```
````

````{dropdown} Option 2: read-only parameter _manager_
Remove the `FitParameters` collection class altogether and use something like
immutable `InitialParameter` instances in the dynamics and intensity section of
the `AmplitudeModel`. The `AmplitudeModel` then starts to serve as a read-only'
template. A fitter package like `tensorwaves` can then loop over the
`AmplitudeModel` structure to extract the `InitialParameter` instances and
convert them to something like an `FitParameter`.

Here's a rough sketch with `tensorwaves` in mind.

```python
from typing import Dict, Generator, List

import attr

from expertsystem.amplitude.model import (
    AmplitudeModel,
    Dynamics,
    Node,
    ParticleDynamics,
)
from expertsystem.particle import Particle


@attr.s
class InitialParameter:
    name: str = attr.ib()
    value: float = attr.ib()
    # fix: bool = attr.ib(default=False)


@attr.s
class FitParameter:
    name: str = attr.ib(on_setattr=attr.setters.frozen)
    value: float = attr.ib()
    fix: bool = attr.ib(default=False)


class FitParameterManager:
    """Manages all fit parameters of the model"""

    def __init__(self, model: AmplitudeModel) -> None:
        self.__model: AmplitudeModel
        self.__parameter_couplings: Dict[str, str]

    @property
    def parameters(self) -> List[FitParameter]:
        initial_parameters = list(__yield_parameter(self.__model))
        self.__apply_couplings()
        return self.__convert(initial_parameters)

    def couple_parameters(self, parameter1: str, parameter2: str) -> None:
        pass

    def __convert(self, params: List[InitialParameter]) -> List[FitParameter]:
        pass


@attr.s
class CustomDynamics(Dynamics):
    parameter: InitialParameter = attr.ib(kw_only=True)

    @staticmethod
    def from_particle(particle: Particle):
        pass


def __yield_parameter(
    instance: object,
) -> Generator[InitialParameter, None, None]:
    if isinstance(instance, InitialParameter):
        yield instance
    elif isinstance(instance, (ParticleDynamics, Node)):
        for item in instance.values():
            yield from __yield_parameter(item)
    elif isinstance(instance, (list,)):
        for item in instance:
            yield from __yield_parameter(item)
    elif attr.has(instance.__class__):
        for field in attr.fields(instance.__class__):
            field_value = getattr(instance, field.name)
            yield from __yield_parameter(field_value)


# usage in tensorwaves
amp_model = AmplitudeModel()
kinematics: HelicityKinematics = ...
builder = IntensityBuilder(kinematics)

intensity = builder.create(amp_model)  # this would call amp_model.parameters
parameters: Dict[str, float] = intensity.parameters
# PROBLEM?: fix status is lost at this point

data_sample = generate_data(...)
dataset = kinematics.convert(data_sample)

parameters["Width_f(0)(980)"] = 0.2  # name is immutable at this point

# name of a parameter can be changed in the AmplitudeModel though
# and then call builder again
intensity(dataset, parameters)
```
````

## Decision Outcome

<!-- TODO -->

<!--
### Positive Consequences

### Negative Consequences
-->

## Pros and Cons of the Options <!-- optional -->

<!--
### [option 1]

[example | description | pointer to more information | …]

- Good, because [argument a]
- Good, because [argument b]
- Bad, because [argument c]

### [option 2]

[example | description | pointer to more information | …]

- Good, because [argument a]
- Good, because [argument b]
- Bad, because [argument c]
- … numbers of pros and cons can vary
-->
