"""The expert system facilitates building an amplitude model.

An amplitude model describes the reaction process you want to study with
partial wave analysis techniques. The responsibility of the expert system is to
give advice on the form of an amplitude model based on the problem set one
defines for a reaction process (initial state, final state, allowed
interactions, intermediate states, etc.). Internally, the system propagates the
quantum numbers through the reaction graph, while satisfying the specified
conservation rules.

Afterwards, the amplitude model of the expert system can be exported. This
amplitude model can then for instance be used to generate a data set (toy Monte
Carlo) for this specific reaction process, or to optimize ('fit') its
parameters so that they resemble the data set as good as possible.
"""


__all__ = [
    "amplitude",
    "particles",
    "io",
    "solving",
    "ui",
]


from . import amplitude, io, particles, solving, ui
