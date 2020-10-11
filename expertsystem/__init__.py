"""A decision-making "expert system" that facilitates Partial Wave Analysis.

The responsibility of the `expertsystem` is to give advice on the form of an
amplitude model based on the problem set one defines for a particle reaction
process (initial state, final state, allowed interactions, intermediate states,
etc.).

The `expertsystem` consists of three main components:

#. `particles`: a stand-alone submodule with which one can investigate specific
   quantum properties of `.Particle` instances (see :doc:`/usage/particles`).

#. `solving`: the core of the `expertsystem` that computes which transitions
   (represented by a `.StateTransitionGraph`) are allowed between a certain
   initial and final state. Internally, the system propagates the quantum
   numbers defined by `particles` through the `.StateTransitionGraph`, while
   satisfying the rules define by the :mod:`.conservation_rules` module.

#. `amplitude`: a collection of tools to convert the `.StateTransitionGraph`
   solutions found by `solving` into an `.AmplitudeModel`. This module is
   specifically designed to create amplitude model templates for PWA fitter
   packages.

Finally, the `.ui` module glues these modules together through facade functions
and the `.StateTransitionManager`, while the `.io` module provides tools that
can read and write the objects of `particles`, `solving`, and `amplitude`.
"""


__all__ = [
    "amplitude",
    "particles",
    "io",
    "solving",
    "ui",
]


from . import amplitude, io, particles, solving, ui
