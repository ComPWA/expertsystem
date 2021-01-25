"""Generate an amplitude model in terms of SymPy objects."""

import logging
import operator
from collections import abc
from functools import reduce
from typing import (
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

import attr
import sympy as sy
from sympy.abc import x
from sympy.physics.quantum.spin import Rotation as Wigner

from expertsystem.particle import Particle, ParticleCollection
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
    get_parent_recoil_edge,
    get_prefactor,
    get_recoil_edge,
    group_graphs_same_initial_and_final,
)
from .kinematics import HelicityKinematics, SubSystem
from .model import Kinematics

ValueType = TypeVar("ValueType", float, complex)


@attr.s(auto_attribs=True)
class _HelicityParticle:
    particle: Particle
    helicity: float


@attr.s
class ParameterProperties(Generic[ValueType]):
    value: ValueType = attr.ib()
    fix: bool = attr.ib(default=False)


@attr.s(on_setattr=attr.setters.frozen)
class SuggestedParameterValues(abc.MutableMapping):
    parameters: Dict[sy.Symbol, ParameterProperties] = attr.ib(default=dict())

    def __delitem__(self, key: Union[sy.Symbol, str]) -> None:
        if isinstance(key, str):
            key = sy.Symbol(key)
        del self.parameters[key]

    def __getitem__(self, key: Union[sy.Symbol, str]) -> ParameterProperties:
        if isinstance(key, str):
            key = sy.Symbol(key)
        return self.parameters[key]

    def __iter__(self) -> sy.Symbol:
        return iter(self.parameters)

    def __len__(self) -> int:
        return len(self.parameters)

    def __setitem__(
        self, key: Union[sy.Symbol, str], value: ParameterProperties
    ) -> None:
        if isinstance(key, str):
            key = sy.Symbol(key)
        if not isinstance(value, ParameterProperties):
            raise ValueError(
                f"Value has to be of type {ParameterProperties.__name__},"
                f" but is of type {value.__class__.__name__}"
            )
        self.parameters[key] = value


@attr.s(kw_only=True)
class SympyModel:  # pylint: disable=too-many-instance-attributes
    top: sy.Expr = attr.ib()
    intensities: Dict[sy.Function, sy.Function] = attr.ib(default=dict())
    amplitudes: Dict[sy.Function, sy.Function] = attr.ib(default=dict())
    dynamics: Dict[sy.Function, sy.Function] = attr.ib(default=dict())

    @property
    def full_expression(self) -> sy.Expr:
        return (
            self.top.subs(self.intensities)
            .subs(self.amplitudes)
            .subs(self.dynamics)
        )


@attr.s(kw_only=True)
class ModelInfo:  # pylint: disable=too-many-instance-attributes
    kinematics: Kinematics = attr.ib(
        validator=attr.validators.instance_of(Kinematics)
    )
    particles: ParticleCollection = attr.ib(
        validator=attr.validators.instance_of(ParticleCollection)
    )
    expression: SympyModel = attr.ib(
        validator=attr.validators.instance_of(SympyModel),
    )
    parameters: SuggestedParameterValues = attr.ib(
        default=SuggestedParameterValues(),
        validator=attr.validators.instance_of(SuggestedParameterValues),
    )


class _SympyHelicityAmplitudeNameGenerator:
    """Parameter name generator for the helicity formalism."""

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
        self.__particles = generate_particle_collection(self.__graphs)
        self.__kinematics = generate_kinematics(reaction_result)
        self.__intensities: Dict[sy.Function, sy.Function] = dict()
        self.__amplitudes: Dict[sy.Function, sy.Function] = dict()
        self.__dynamics: Dict[sy.Function, sy.Function] = dict()
        self.__parameters = SuggestedParameterValues()

    def generate(self) -> ModelInfo:
        top = self.__generate_intensities()
        return ModelInfo(
            particles=self.__particles,
            kinematics=self.__kinematics,
            expression=SympyModel(
                top=top,
                intensities=self.__intensities,
                amplitudes=self.__amplitudes,
                dynamics=self.__dynamics,
            ),
            parameters=self.__parameters,
        )

    def __generate_intensities(self) -> sy.Expr:
        graph_groups = group_graphs_same_initial_and_final(self.__graphs)
        logging.debug("There are %d graph groups", len(graph_groups))

        self.__create_parameter_couplings(graph_groups)
        coherent_intensities = [
            self.__generate_coherent_intensity(graph_group)
            for graph_group in graph_groups
        ]
        if len(coherent_intensities) == 0:
            raise ValueError("List of coherent intensities cannot be empty")
        if len(coherent_intensities) == 1:
            return coherent_intensities[0]
        return sum(coherent_intensities)

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
        symbol = sy.Function(fR"I[{graph_group_label}]")(x)
        expression: List[sy.Expr] = list()
        for graph in graph_group:
            sequential_graphs = (
                perform_external_edge_identical_particle_combinatorics(graph)
            )
            for seq_graph in sequential_graphs:
                expression.append(self.__generate_sequential_decay(seq_graph))
        amplitude_sum = sum(expression)
        coherent_intensity = sy.conjugate(amplitude_sum) * amplitude_sum
        self.__intensities[symbol] = coherent_intensity
        return symbol

    def __generate_sequential_decay(
        self, graph: StateTransitionGraph[ParticleWithSpin]
    ) -> sy.Symbol:
        partial_decays_symbols: List[sy.Symbol] = [
            self._generate_partial_decay(graph, node_id)
            for node_id in graph.topology.nodes
        ]
        sequential_amplitudes = reduce(operator.mul, partial_decays_symbols)

        symbol = sy.Function(
            f"A[{self.name_generator.generate_unique_amplitude_name(graph)}]"
        )(x)
        coefficient = self.__generate_amplitude_coefficient(graph)
        prefactor = self.__generate_amplitude_prefactor(graph)
        expression = coefficient * sequential_amplitudes
        if prefactor is not None:
            expression = prefactor * expression
        self.__amplitudes[symbol] = expression
        return symbol

    def _generate_partial_decay(  # pylint: disable=too-many-locals
        self, graph: StateTransitionGraph[ParticleWithSpin], node_id: int
    ) -> sy.Symbol:
        in_edge_ids = graph.topology.get_edge_ids_ingoing_to_node(node_id)
        out_edge_ids = graph.topology.get_edge_ids_outgoing_from_node(node_id)
        if len(in_edge_ids) != 1 or len(out_edge_ids) != 2:
            raise ValueError(
                f"Node {node_id} does not represent a 1-to-2 body decay!"
            )

        edge_id = next(iter(in_edge_ids))
        parent = _HelicityParticle(*graph.get_edge_props(edge_id))
        children: List[_HelicityParticle] = list()
        decay_products_fs_ids_list: List[List[int]] = list()
        for out_edge_id in out_edge_ids:
            edge_props = graph.get_edge_props(out_edge_id)
            children.append(_HelicityParticle(*edge_props))
            final_state_ids = determine_attached_final_state(
                graph.topology, out_edge_id
            )
            decay_products_fs_ids_list.append(final_state_ids)
        decay_products_fs_ids: Tuple[Tuple[int, ...], Tuple[int, ...]] = (
            tuple(decay_products_fs_ids_list[0]),
            tuple(decay_products_fs_ids_list[1]),
        )

        recoil_final_state: Tuple[int, ...] = tuple()
        parent_recoil_final_state: Tuple[int, ...] = tuple()

        in_edge_id = next(iter(in_edge_ids))
        ingoing_edge_id = in_edge_id
        recoil_edge_id = get_recoil_edge(graph.topology, ingoing_edge_id)
        if recoil_edge_id is not None:
            recoil_final_state = tuple(
                determine_attached_final_state(graph.topology, recoil_edge_id)
            )
            parent_recoil_edge_id = get_parent_recoil_edge(
                graph.topology, ingoing_edge_id
            )
            if parent_recoil_edge_id is not None:
                parent_recoil_final_state = tuple(
                    determine_attached_final_state(
                        graph.topology, parent_recoil_edge_id
                    )
                )
        inv_mass, theta, phi = self.__generate_kinematic_variables(
            decay_products_fs_ids,
            recoil_final_state,
            parent_recoil_final_state,
        )

        wigner_d = Wigner.D(
            j=sy.nsimplify(parent.particle.spin),
            m=sy.nsimplify(parent.helicity),
            mp=sy.nsimplify(children[0].helicity - children[1].helicity),
            alpha=-phi,
            beta=theta,
            gamma=0,
        )
        decay_product_description = " ".join(
            child.particle.name
            if child.particle.latex is None
            else child.particle.latex
            for child in children
        )
        parent_label = (
            parent.particle.name
            if parent.particle.latex is None
            else parent.particle.latex
        )
        dynamics = sy.Function(
            fR"D[{parent_label} \to {decay_product_description}]"
        )(inv_mass)
        suggested_dynamics = 1
        self.__dynamics[dynamics] = suggested_dynamics
        return wigner_d * dynamics

    def __generate_kinematic_variables(  # pylint: disable=no-self-use,unused-argument
        self,
        decay_products_final_state_ids: Tuple[
            Tuple[int, ...], Tuple[int, ...]
        ],
        recoil_final_state_ids: Tuple[int, ...],
        parent_recoil_final_state_ids: Tuple[int, ...],
    ) -> Tuple[sy.Symbol, sy.Symbol, sy.Symbol]:
        """Generate kinematic sympy variables of a helicity decay.

        Kinematic variables are:
        - invariant mass
        - helicity angle theta
        - helicity angle phi
        """
        kinematics = HelicityKinematics(reaction_info=self.__kinematics)
        subsystem = SubSystem(
            final_states=decay_products_final_state_ids,
            recoil_state=recoil_final_state_ids,
            parent_recoil_state=parent_recoil_final_state_ids,
        )
        inv_mass, theta, phi = kinematics.register_subsystem(subsystem)
        return (
            sy.Symbol(inv_mass, real=True),
            sy.Symbol(theta, real=True),
            sy.Symbol(phi, real=True),
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
        self.__parameters[coefficient_symbol] = ParameterProperties(
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
