"""Generate an amplitude model in terms of SymPy objects."""

import logging
import operator
from collections import abc, defaultdict
from functools import reduce
from typing import (
    Dict,
    Generic,
    ItemsView,
    Iterable,
    KeysView,
    List,
    Mapping,
    Optional,
    Tuple,
    TypeVar,
    Union,
    ValuesView,
)

import attr
import sympy as sy
from sympy.physics.quantum.cg import CG
from sympy.physics.quantum.spin import Rotation as Wigner

from expertsystem.particle import Particle, ParticleCollection, Spin
from expertsystem.reaction import Result
from expertsystem.reaction.combinatorics import (
    perform_external_edge_identical_particle_combinatorics,
)
from expertsystem.reaction.quantum_numbers import ParticleWithSpin
from expertsystem.reaction.topology import StateTransitionGraph

from ._graph_info import (
    determine_attached_final_state,
    generate_kinematics,
    generate_particle_collection,
    get_angular_momentum,
    get_coupled_spin,
    get_parent_recoil_edge,
    get_prefactor,
    get_recoil_edge,
    group_graphs_same_initial_and_final,
)
from .kinematics import generate_kinematic_variables
from .model import Kinematics

ValueType = TypeVar("ValueType", float, complex, int)


@attr.s(frozen=True)
class State:
    particle: Particle = attr.ib(
        validator=attr.validators.instance_of(Particle)
    )
    spin_projection: float = attr.ib(converter=float)


@attr.s(frozen=True, auto_attribs=True)
class _EdgeWithState:
    edge_id: int
    state: State

    @classmethod
    def from_graph(
        cls, graph: StateTransitionGraph, edge_id: int
    ) -> "_EdgeWithState":
        particle, spin_projection = graph.get_edge_props(edge_id)
        return cls(
            edge_id=edge_id,
            state=State(
                particle=particle,
                spin_projection=spin_projection,
            ),
        )


@attr.s(frozen=True, auto_attribs=True)
class _TwoBodyDecay:
    parent: _EdgeWithState
    children: Tuple[_EdgeWithState, _EdgeWithState]

    @classmethod
    def from_graph(
        cls, graph: StateTransitionGraph[ParticleWithSpin], node_id: int
    ) -> "_TwoBodyDecay":
        in_edge_ids = graph.topology.get_edge_ids_ingoing_to_node(node_id)
        out_edge_ids = graph.topology.get_edge_ids_outgoing_from_node(node_id)
        if len(in_edge_ids) != 1 or len(out_edge_ids) != 2:
            raise ValueError(
                f"Node {node_id} does not represent a 1-to-2 body decay!"
            )

        ingoing_edge_id = next(iter(in_edge_ids))
        out_edge_id1, out_edge_id2 = tuple(out_edge_ids)
        return cls(
            parent=_EdgeWithState.from_graph(graph, ingoing_edge_id),
            children=(
                _EdgeWithState.from_graph(graph, out_edge_id1),
                _EdgeWithState.from_graph(graph, out_edge_id2),
            ),
        )


@attr.s
class ParameterProperties(Generic[ValueType]):
    value: ValueType = attr.ib()
    fix: bool = attr.ib(default=False)


class SuggestedParameterValues(abc.MutableMapping):
    def __init__(
        self,
        parameters: Optional[
            Mapping[
                Union[sy.Symbol, str],
                Union[ParameterProperties, complex, float],
            ]
        ] = None,
    ) -> None:
        self.__parameters: Dict[sy.Symbol, ParameterProperties] = dict()
        if parameters is not None:
            if not isinstance(parameters, abc.Mapping):
                raise TypeError(
                    f"{self.__class__.__name__} requires a mapping"
                )
            if not all(
                map(lambda k: isinstance(k, (sy.Symbol, str)), parameters)
            ):
                raise TypeError(
                    f"Not all keys are of type {sy.Symbol.__class__} or str"
                )
            if not all(
                map(
                    lambda v: isinstance(
                        v, (ParameterProperties, complex, float)
                    ),
                    parameters.values(),
                )
            ):
                raise TypeError(
                    "Not all values are of type"
                    f" {ParameterProperties.__class__} or complex or float"
                )
            for par, value in parameters.items():
                if isinstance(par, sy.Symbol):
                    par_symbol = par
                else:
                    par_symbol = sy.Symbol(par)
                if isinstance(value, ParameterProperties):
                    par_value = value
                else:
                    par_value = ParameterProperties(value)
                self.__parameters[par_symbol] = par_value

    def __delitem__(self, key: Union[sy.Symbol, str]) -> None:
        if isinstance(key, str):
            key = sy.Symbol(key)
        del self.__parameters[key]

    def __getitem__(self, key: Union[sy.Symbol, str]) -> ParameterProperties:
        if isinstance(key, str):
            key = sy.Symbol(key)
        return self.__parameters[key]

    def __iter__(self) -> sy.Symbol:
        return iter(self.__parameters)

    def __len__(self) -> int:
        return len(self.__parameters)

    def __repr__(self) -> str:
        str_dict = {p.name: v for p, v in self.items()}
        return f"{self.__class__.__name__}({str_dict})"

    def __setitem__(
        self, key: Union[sy.Symbol, str], value: ParameterProperties
    ) -> None:
        if isinstance(key, str):
            key = sy.Symbol(key)
        if not isinstance(value, ParameterProperties):
            if not isinstance(
                value,
                ValueType.__constraints__,  # type: ignore  # pylint: disable=no-member
            ):
                raise ValueError(
                    f"Cannot convert {value.__class__.__name__}"
                    f" to {ParameterProperties.__name__}"
                )
            value = ParameterProperties(value)
        self.__parameters[key] = value

    def keys(self) -> KeysView[sy.Symbol]:
        return self.__parameters.keys()

    def items(self) -> ItemsView[sy.Symbol, ParameterProperties]:
        return self.__parameters.items()

    def values(self) -> ValuesView[ParameterProperties]:
        return self.__parameters.values()

    def subs_values(self) -> Dict[sy.Symbol, Union[complex, float]]:
        return {p: v.value for p, v in self.items()}


@attr.s(kw_only=True)
class SympyModel:  # pylint: disable=too-many-instance-attributes
    top: sy.Expr = attr.ib()
    intensities: Dict[sy.Symbol, sy.Expr] = attr.ib(factory=dict)
    amplitudes: Dict[sy.Symbol, sy.Expr] = attr.ib(factory=dict)
    dynamics: Dict[sy.Symbol, sy.Expr] = attr.ib(factory=dict)

    @property
    def full_expression(self) -> sy.Expr:
        return (
            self.top.subs(self.intensities)
            .subs(self.amplitudes)
            .subs(self.dynamics)
        )


@attr.s(kw_only=True)
class ModelInfo:  # pylint: disable=too-many-instance-attributes
    transitions: List[StateTransitionGraph[ParticleWithSpin]] = attr.ib(
        on_setattr=attr.setters.frozen
    )
    expression: SympyModel = attr.ib(
        validator=attr.validators.instance_of(SympyModel),
    )
    parameters: SuggestedParameterValues = attr.ib(
        validator=attr.validators.instance_of(SuggestedParameterValues),
        init=False,
    )
    kinematics: Kinematics = attr.ib(
        validator=attr.validators.instance_of(Kinematics),
        init=False,
    )
    particles: ParticleCollection = attr.ib(
        validator=attr.validators.instance_of(ParticleCollection),
        init=False,
    )
    dynamics_parameters: Dict[sy.Symbol, Dict[sy.Symbol, float]] = attr.ib(
        factory=lambda: defaultdict(dict),
        init=False,
    )

    def __attrs_post_init__(self) -> None:
        self.parameters = SuggestedParameterValues()
        self.kinematics = generate_kinematics(self.transitions)
        self.particles = generate_particle_collection(self.transitions)

    def set_dynamics(
        self,
        graph: StateTransitionGraph[ParticleWithSpin],
        node_id: int,
        expression: sy.Expr,
        parameters: Dict[sy.Symbol, float],
    ) -> sy.Symbol:
        decay = _TwoBodyDecay.from_graph(graph, node_id)
        decay_product_description = " ".join(
            child.state.particle.name
            if child.state.particle.latex is None
            else child.state.particle.latex
            for child in decay.children
        )
        parent_label = (
            decay.parent.state.particle.name
            if decay.parent.state.particle.latex is None
            else decay.parent.state.particle.latex
        )
        dynamics_symbol = sy.Symbol(
            fR"D[{parent_label} \to {decay_product_description}]"
        )
        self.expression.dynamics[dynamics_symbol] = expression

        # update parameter dictionaries
        new_parameters = SuggestedParameterValues(
            {
                k: v
                for k, v in self.parameters.items()
                if k not in self.dynamics_parameters[dynamics_symbol]
            }
        )
        for par, value in parameters.items():
            new_parameters[par] = ParameterProperties[float](value, False)
        self.parameters = new_parameters
        self.dynamics_parameters[dynamics_symbol] = parameters

        return dynamics_symbol


class _SympyHelicityAmplitudeNameGenerator:
    def __init__(self) -> None:
        self.parity_partner_coefficient_mapping: Dict[str, str] = {}

    def _generate_amplitude_coefficient_couple(
        self, graph: StateTransitionGraph[ParticleWithSpin], node_id: int
    ) -> Tuple[str, str, str]:
        (in_hel_info, out_hel_info) = self._retrieve_helicity_info(
            graph, node_id
        )
        par_name_suffix = self.generate_amplitude_coefficient_name(
            graph, node_id
        )

        pp_par_name_suffix = (
            _generate_particles_string(in_hel_info, False)
            + R" \to "
            + _generate_particles_string(
                out_hel_info, make_parity_partner=True
            )
        )

        priority_name_suffix = par_name_suffix
        if out_hel_info[0][1] < 0 or (
            out_hel_info[0][1] == 0 and out_hel_info[1][1] < 0
        ):
            priority_name_suffix = pp_par_name_suffix

        return (par_name_suffix, pp_par_name_suffix, priority_name_suffix)

    def register_amplitude_coefficient_name(
        self, graph: StateTransitionGraph[ParticleWithSpin]
    ) -> None:
        for node_id in graph.topology.nodes:
            (
                coefficient_suffix,
                parity_partner_coefficient_suffix,
                priority_partner_coefficient_suffix,
            ) = self._generate_amplitude_coefficient_couple(graph, node_id)

            if graph.get_node_props(node_id).parity_prefactor is None:
                continue

            if (
                coefficient_suffix
                not in self.parity_partner_coefficient_mapping
            ):
                if (
                    parity_partner_coefficient_suffix
                    in self.parity_partner_coefficient_mapping
                ):
                    if (
                        parity_partner_coefficient_suffix
                        == priority_partner_coefficient_suffix
                    ):
                        self.parity_partner_coefficient_mapping[
                            coefficient_suffix
                        ] = parity_partner_coefficient_suffix
                    else:
                        self.parity_partner_coefficient_mapping[
                            parity_partner_coefficient_suffix
                        ] = coefficient_suffix
                        self.parity_partner_coefficient_mapping[
                            coefficient_suffix
                        ] = coefficient_suffix

                else:
                    # if neither this coefficient nor its partner are registered just add it
                    self.parity_partner_coefficient_mapping[
                        coefficient_suffix
                    ] = coefficient_suffix

    def generate_unique_amplitude_name(
        self,
        graph: StateTransitionGraph[ParticleWithSpin],
        node_id: Optional[int] = None,
    ) -> str:
        """Generates a unique name for the amplitude corresponding.

        That is, corresponging to the given :class:`StateTransitionGraph`. If
        ``node_id`` is given, it generates a unique name for the partial
        amplitude corresponding to the interaction node of the given
        :class:`StateTransitionGraph`.
        """
        name = ""
        if isinstance(node_id, int):
            nodelist = frozenset({node_id})
        else:
            nodelist = graph.topology.nodes
        for node in nodelist:
            (in_hel_info, out_hel_info) = self._retrieve_helicity_info(
                graph, node
            )

            name += (
                _generate_particles_string(in_hel_info)
                + R" \to "
                + _generate_particles_string(out_hel_info)
                + ";"
            )
        return name[:-1]

    @staticmethod
    def _retrieve_helicity_info(
        graph: StateTransitionGraph[ParticleWithSpin], node_id: int
    ) -> Tuple[List[ParticleWithSpin], List[ParticleWithSpin]]:
        in_edges = graph.topology.get_edge_ids_ingoing_to_node(node_id)
        out_edges = graph.topology.get_edge_ids_outgoing_from_node(node_id)

        in_names_hel_list = _get_helicity_particles(graph, in_edges)
        out_names_hel_list = _get_helicity_particles(graph, out_edges)

        return (in_names_hel_list, out_names_hel_list)

    def generate_amplitude_coefficient_name(
        self, graph: StateTransitionGraph[ParticleWithSpin], node_id: int
    ) -> str:
        """Generate partial amplitude coefficient name suffix."""
        in_hel_info, out_hel_info = self._retrieve_helicity_info(
            graph, node_id
        )
        return (
            _generate_particles_string(in_hel_info, False)
            + R" \to "
            + _generate_particles_string(out_hel_info)
        )

    def generate_sequential_amplitude_suffix(
        self, graph: StateTransitionGraph[ParticleWithSpin]
    ) -> str:
        """Generate unique suffix for a sequential amplitude graph."""
        output_suffix = ""
        for node_id in graph.topology.nodes:
            suffix = self.generate_amplitude_coefficient_name(graph, node_id)
            if suffix in self.parity_partner_coefficient_mapping:
                suffix = self.parity_partner_coefficient_mapping[suffix]
            output_suffix += suffix + ";"
        return output_suffix[:-1]


class _SympyCanonicalAmplitudeNameGenerator(
    _SympyHelicityAmplitudeNameGenerator
):
    def generate_unique_amplitude_name(
        self,
        graph: StateTransitionGraph[ParticleWithSpin],
        node_id: Optional[int] = None,
    ) -> str:
        name = ""
        if isinstance(node_id, int):
            node_ids = frozenset({node_id})
        else:
            node_ids = graph.topology.nodes
        for node in node_ids:
            helicity_name = super().generate_unique_amplitude_name(graph, node)
            name += (
                helicity_name[:-1]
                + self._generate_clebsch_gordan_string(graph, node)
                + helicity_name[-1]
                + ";"
            )
        return name

    @staticmethod
    def _generate_clebsch_gordan_string(
        graph: StateTransitionGraph[ParticleWithSpin], node_id: int
    ) -> str:
        node_props = graph.get_node_props(node_id)
        ang_orb_mom = sy.Rational(get_angular_momentum(node_props).magnitude)
        spin = sy.Rational(get_coupled_spin(node_props).magnitude)
        return f",L={ang_orb_mom},S={spin}"


def _get_graph_group_unique_label(
    graph_group: List[StateTransitionGraph[ParticleWithSpin]],
) -> str:
    label = ""
    if graph_group:
        first_graph = next(iter(graph_group))
        ise = first_graph.topology.incoming_edge_ids
        fse = first_graph.topology.outgoing_edge_ids
        is_names = _get_helicity_particles(first_graph, ise)
        fs_names = _get_helicity_particles(first_graph, fse)
        label += (
            _generate_particles_string(is_names)
            + R" \to "
            + _generate_particles_string(fs_names)
        )
    return label


def _get_helicity_particles(
    graph: StateTransitionGraph[ParticleWithSpin], edge_ids: Iterable[int]
) -> List[ParticleWithSpin]:
    helicity_list: List[ParticleWithSpin] = []
    for i in edge_ids:
        particle, spin_projection = graph.get_edge_props(i)
        if isinstance(spin_projection, float) and spin_projection.is_integer():
            spin_projection = int(spin_projection)
        helicity_list.append((particle, spin_projection))

    # in order to ensure correct naming of amplitude coefficients the list has
    # to be sorted by name. The same coefficient names have to be created for
    # two graphs that only differ from a kinematic standpoint
    # (swapped external edges)
    return sorted(helicity_list, key=lambda entry: entry[0].name)


def _generate_particles_string(
    helicity_list: List[ParticleWithSpin],
    use_helicity: bool = True,
    make_parity_partner: bool = False,
) -> str:
    output_string = ""
    for particle, spin_projection in helicity_list:
        if particle.latex is not None:
            output_string += particle.latex
        else:
            output_string += particle.name
        if use_helicity:
            if make_parity_partner:
                helicity = -1 * spin_projection
            else:
                helicity = spin_projection
            if helicity > 0:
                helicity_str = f"+{helicity}"
            else:
                helicity_str = str(helicity)
            output_string += f"_{{{helicity_str}}}"
        output_string += " "
    return output_string[:-1]


def _generate_kinematic_variables(
    graph: StateTransitionGraph[ParticleWithSpin], node_id: int
) -> Tuple[sy.Symbol, sy.Symbol, sy.Symbol]:
    decay = _TwoBodyDecay.from_graph(graph, node_id)
    decay_products_fs_ids = (
        tuple(
            determine_attached_final_state(
                graph.topology, decay.children[0].edge_id
            )
        ),
        tuple(
            determine_attached_final_state(
                graph.topology, decay.children[1].edge_id
            )
        ),
    )

    recoil_final_state: Tuple[int, ...] = tuple()
    parent_recoil_final_state: Tuple[int, ...] = tuple()

    recoil_edge_id = get_recoil_edge(graph.topology, decay.parent.edge_id)
    if recoil_edge_id is not None:
        recoil_final_state = tuple(
            determine_attached_final_state(graph.topology, recoil_edge_id)
        )
        parent_recoil_edge_id = get_parent_recoil_edge(
            graph.topology, decay.parent.edge_id
        )
        if parent_recoil_edge_id is not None:
            parent_recoil_final_state = tuple(
                determine_attached_final_state(
                    graph.topology, parent_recoil_edge_id
                )
            )
    return sy.symbols(
        generate_kinematic_variables(
            decay_products_fs_ids,
            recoil_final_state,
            parent_recoil_final_state,
        ),
        real=True,
    )


class SympyHelicityAmplitudeGenerator:  # pylint: disable=too-many-instance-attributes
    """Amplitude model generator for the helicity formalism."""

    def __init__(self, reaction_result: Result) -> None:
        self.name_generator = _SympyHelicityAmplitudeNameGenerator()
        self.__graphs = reaction_result.transitions
        if len(self.__graphs) < 1:
            raise ValueError(
                f"At least one {StateTransitionGraph.__name__} required to"
                " genenerate an amplitude model!"
            )

        get_initial_state = reaction_result.get_initial_state()
        if len(get_initial_state) != 1:
            raise ValueError(
                "Helicity amplitude model requires exactly one initial state"
            )
        self.__initialize_model()

    def __initialize_model(self) -> None:
        self.__model = ModelInfo(
            transitions=self.__graphs,
            expression=SympyModel(top=1),
        )

    def generate(self) -> ModelInfo:
        self.__initialize_model()
        self.__generate_intensities()
        return self.__model

    def __generate_intensities(self) -> sy.Expr:
        graph_groups = group_graphs_same_initial_and_final(self.__graphs)
        logging.debug("There are %d graph groups", len(graph_groups))

        self.__create_parameter_couplings(graph_groups)
        for graph_group in graph_groups:
            self.__generate_coherent_intensity(graph_group)
        coherent_intensities = self.__model.expression.intensities
        if len(coherent_intensities) == 0:
            raise ValueError("List of coherent intensities cannot be empty")
        self.__model.expression.top = sum(coherent_intensities)
        return self.__model.expression.top

    def __create_parameter_couplings(
        self, graph_groups: List[List[StateTransitionGraph[ParticleWithSpin]]]
    ) -> None:
        for graph_group in graph_groups:
            for graph in graph_group:
                self.name_generator.register_amplitude_coefficient_name(graph)

    def __generate_coherent_intensity(
        self,
        graph_group: List[StateTransitionGraph[ParticleWithSpin]],
    ) -> sy.Symbol:
        graph_group_label = _get_graph_group_unique_label(graph_group)
        symbol = sy.Symbol(fR"I[{graph_group_label}]")
        expression: List[sy.Expr] = list()
        for graph in graph_group:
            sequential_graphs = (
                perform_external_edge_identical_particle_combinatorics(graph)
            )
            for seq_graph in sequential_graphs:
                expression.append(self.__generate_sequential_decay(seq_graph))
        amplitude_sum = sum(expression)
        coherent_intensity = abs(amplitude_sum) ** 2
        self.__model.expression.intensities[symbol] = coherent_intensity
        return symbol

    def __generate_sequential_decay(
        self, graph: StateTransitionGraph[ParticleWithSpin]
    ) -> sy.Symbol:
        partial_decays_symbols: List[sy.Symbol] = [
            self._generate_partial_decay(graph, node_id)
            for node_id in graph.topology.nodes
        ]
        sequential_amplitudes = reduce(operator.mul, partial_decays_symbols)

        symbol = sy.Symbol(
            f"A[{self.name_generator.generate_unique_amplitude_name(graph)}]"
        )
        coefficient = self.__generate_amplitude_coefficient(graph)
        prefactor = self.__generate_amplitude_prefactor(graph)
        expression = coefficient * sequential_amplitudes
        if prefactor is not None:
            expression = prefactor * expression
        self.__model.expression.amplitudes[symbol] = expression
        return symbol

    def _generate_partial_decay(  # pylint: disable=too-many-locals
        self, graph: StateTransitionGraph[ParticleWithSpin], node_id: int
    ) -> sy.Symbol:
        wigner_d = self._generate_wigner_d(graph, node_id)
        suggested_dynamics = 1
        dynamics_symbol = self.__model.set_dynamics(
            graph, node_id, suggested_dynamics, {}
        )
        return wigner_d * dynamics_symbol

    @staticmethod
    def _generate_wigner_d(
        graph: StateTransitionGraph[ParticleWithSpin], node_id: int
    ) -> sy.Symbol:
        decay = _TwoBodyDecay.from_graph(graph, node_id)
        _, theta, phi = _generate_kinematic_variables(graph, node_id)

        return Wigner.D(
            j=sy.nsimplify(decay.parent.state.particle.spin),
            m=sy.nsimplify(decay.parent.state.spin_projection),
            mp=sy.nsimplify(
                decay.children[0].state.spin_projection
                - decay.children[1].state.spin_projection
            ),
            alpha=-phi,
            beta=theta,
            gamma=0,
        )

    def __generate_amplitude_coefficient(
        self, graph: StateTransitionGraph[ParticleWithSpin]
    ) -> sy.Symbol:
        """Generate coefficient parameter for a sequential amplitude graph.

        Generally, each partial amplitude of a sequential amplitude graph
        should check itself if it or a parity partner is already defined. If so
        a coupled coefficient is introduced.
        """
        suffix = self.name_generator.generate_sequential_amplitude_suffix(
            graph
        )
        coefficient_symbol = sy.Symbol(f"C[{suffix}]")
        self.__model.parameters[coefficient_symbol] = ParameterProperties(
            complex(1, 0), fix=False
        )
        return coefficient_symbol

    def __generate_amplitude_prefactor(
        self, graph: StateTransitionGraph[ParticleWithSpin]
    ) -> Optional[float]:
        prefactor = get_prefactor(graph)
        if prefactor != 1.0:
            for node_id in graph.topology.nodes:
                raw_suffix = (
                    self.name_generator.generate_amplitude_coefficient_name(
                        graph, node_id
                    )
                )
                if (
                    raw_suffix
                    in self.name_generator.parity_partner_coefficient_mapping
                ):
                    coefficient_suffix = (
                        self.name_generator.parity_partner_coefficient_mapping[
                            raw_suffix
                        ]
                    )
                    if coefficient_suffix != raw_suffix:
                        return prefactor
        return None


class SympyCanonicalAmplitudeGenerator(SympyHelicityAmplitudeGenerator):
    r"""Amplitude model generator for the canonical helicity formalism.

    This class defines a full amplitude in the canonical formalism, using the
    helicity formalism as a foundation. The key here is that we take the full
    helicity intensity as a template, and just exchange the helicity amplitudes
    :math:`F` as a sum of canonical amplitudes :math:`A`:

    .. math::

        F^J_{\lambda_1,\lambda_2} = \sum_{LS} \mathrm{norm}(A^J_{LS})C^2.

    Here, :math:`C` stands for `Clebsch-Gordan factor
    <https://en.wikipedia.org/wiki/Clebsch%E2%80%93Gordan_coefficients>`_.
    """

    def __init__(self, reaction_result: Result) -> None:
        super().__init__(reaction_result)
        self.name_generator = _SympyCanonicalAmplitudeNameGenerator()

    def _generate_partial_decay(  # pylint: disable=too-many-locals
        self, graph: StateTransitionGraph[ParticleWithSpin], node_id: int
    ) -> sy.Symbol:
        amplitude = super()._generate_partial_decay(graph, node_id)

        node_props = graph.get_node_props(node_id)
        ang_mom = get_angular_momentum(node_props)
        spin = get_coupled_spin(node_props)
        if ang_mom.projection != 0.0:
            raise ValueError(f"Projection of L is non-zero!: {ang_mom}")

        topology = graph.topology
        in_edge_ids = topology.get_edge_ids_ingoing_to_node(node_id)
        out_edge_ids = topology.get_edge_ids_outgoing_from_node(node_id)

        in_edge_id = next(iter(in_edge_ids))
        particle, spin_projection = graph.get_edge_props(in_edge_id)
        parent_spin = Spin(
            particle.spin,
            spin_projection,
        )

        daughter_spins: List[Spin] = []
        for out_edge_id in out_edge_ids:
            particle, spin_projection = graph.get_edge_props(out_edge_id)
            daughter_spin = Spin(
                particle.spin,
                spin_projection,
            )
            if daughter_spin is not None and isinstance(daughter_spin, Spin):
                daughter_spins.append(daughter_spin)

        decay_particle_lambda = (
            daughter_spins[0].projection - daughter_spins[1].projection
        )

        cg_ls = CG(
            j1=sy.nsimplify(ang_mom.magnitude),
            m1=sy.nsimplify(ang_mom.projection),
            j2=sy.nsimplify(spin.magnitude),
            m2=sy.nsimplify(decay_particle_lambda),
            j3=sy.nsimplify(parent_spin.magnitude),
            m3=sy.nsimplify(decay_particle_lambda),
        )
        cg_ss = CG(
            j1=sy.nsimplify(daughter_spins[0].magnitude),
            m1=sy.nsimplify(daughter_spins[0].projection),
            j2=sy.nsimplify(daughter_spins[1].magnitude),
            m2=sy.nsimplify(-daughter_spins[1].projection),
            j3=sy.nsimplify(spin.magnitude),
            m3=sy.nsimplify(decay_particle_lambda),
        )
        return cg_ls * cg_ss * amplitude