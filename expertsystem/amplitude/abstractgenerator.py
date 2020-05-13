"""Collection of abstract interfaces for amplitude model generation."""


from abc import ABC
from abc import abstractmethod

from typing import Tuple


class AbstractAmplitudeNameGenerator(ABC):
    """Interface for creating strings for the :class:`StateTransitionGraph`."""

    @abstractmethod
    def generate_unique_amplitude_name(self, graph: list, node_id: int) -> str:
        """
        Generate a unique name for the amplitude.

        The name corresponds to the given none give in
        :class:`StateTransitionGraph`. If ``node_id`` is given, it generates a
        unique name for the partial amplitude corresponding to the interaction
        node of the given :class:`StateTransitionGraph`.
        """

    @abstractmethod
    def generate_amplitude_coefficient_infos(self, graph: list) -> dict:
        """Generate coefficient info for a sequential amplitude graph."""

    @abstractmethod
    def _generate_amplitude_coefficient_names(
        self, graph: list, node_id: int
    ) -> Tuple[str, str]:
        pass


class AbstractAmplitudeGenerator(ABC):
    """Abstract interface that handles amplitude model generation."""

    @abstractmethod
    def generate(self, graphs: list) -> None:
        """
        Generate an amplitude model from a given `list` of graphs.

        The result is stored internally.
        """

    @abstractmethod
    def write_to_file(self, filename: str) -> None:
        """
        Write generated amplitude model to a recipe file.

        This function can only be called to be called *after*
        `~.AbstractAmplitudeGenerator.generate`.
        """
