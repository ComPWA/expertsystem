# cspell:ignore nsimplify
# pylint: disable=redefined-outer-name,no-self-use

from typing import Any, List, Optional, Sequence, Union

import pytest
import sympy as sy

import expertsystem as es
from expertsystem.particle import ParticleCollection


def calculate_sympy_integral(
    intensity: Any,
    integration_variables: List[sy.Symbol],
    jacobi_determinant: Optional[Any] = None,
) -> sy.Expr:
    if jacobi_determinant is None:
        for int_var in integration_variables:
            if "theta" in int_var.name:
                intensity *= sy.sin(int_var)
    else:
        intensity *= jacobi_determinant
    return sy.trigsimp(
        sy.nsimplify(
            sy.re(
                sy.integrate(
                    intensity,
                    *(
                        (x, -sy.pi, sy.pi)
                        if "phi" in x.name
                        else (x, 0, sy.pi)
                        for x in integration_variables
                    ),
                )
            ).doit(),
            rational=True,
        )
    )


def normalize(
    sympy_expression: sy.Expr, variable_names: Sequence[str]
) -> sy.Expr:
    variables = [sy.Symbol(x, real=True) for x in variable_names]
    normalization = sy.integrate(
        sympy_expression,
        *(
            (x, -sy.pi, sy.pi) if "phi" in x.name else (x, 0, sy.pi)
            for x in variables
        ),
    )
    return sy.trigsimp((sympy_expression / normalization).expand(trig=True))


class TestEpemToDmD0Pip:
    @pytest.fixture(scope="class")
    def sympy_model(self, particle_database: ParticleCollection) -> sy.Expr:
        epem = es.particle.Particle(
            name="EpEm",
            pid=12345678,
            mass=4.36,
            spin=1.0,
            parity=es.particle.Parity(-1),
            c_parity=es.particle.Parity(-1),
        )
        particles = ParticleCollection(particle_database)
        particles.add(epem)

        result = es.generate_transitions(
            initial_state=[("EpEm", [-1])],
            final_state=[("D0", [0]), ("D-", [0]), ("pi+", [0])],
            allowed_intermediate_particles=["D(2)*(2460)+"],
            allowed_interaction_types="em",
            particles=particles,
        )

        amplitude_model = es.amplitude.generate(result)
        sympy_model = amplitude_model.expression
        sympy_model.dynamics = {k: 1 for k in sympy_model.dynamics.keys()}
        full_model = sy.simplify(
            sympy_model.full_expression.subs(
                {k: p.value for k, p in amplitude_model.parameters.items()}
            )
            .doit()
            .expand(complex=True)
        )
        assert sy.im(full_model) == 0
        return sy.re(full_model)

    @pytest.mark.parametrize(
        "angular_variables, expected_distribution_function",  # type: ignore
        [
            (  # cos(theta) distribution from epem decay
                "theta_0_1+2",
                1 + sy.cos(sy.Symbol("theta_0_1+2", real=True)) ** 2,
            ),
            (  # phi distribution of the epem decay
                "phi_1+2_0",
                1,
            ),
            (  # cos(theta') distribution from D2*
                "theta_1_2_vs_0",
                1
                - (2 * sy.cos(sy.Symbol("theta_1_2_vs_0", real=True)) ** 2 - 1)
                ** 2,
            ),
            (  # phi' distribution of the D2* decay
                "phi_1_2_vs_0",
                3 - 2 * sy.sin(sy.Symbol("phi_1_2_vs_0", real=True)) ** 2,
            ),
            (  # 2d distribution of the D2* decay
                ["theta_1_2_vs_0", "phi_1_2_vs_0"],
                (1 - sy.cos(sy.Symbol("theta_1_2_vs_0", real=True)) ** 2)
                * (sy.cos(sy.Symbol("theta_1_2_vs_0", real=True)) ** 2)
                * (2 + sy.cos(2 * sy.Symbol("phi_1_2_vs_0", real=True))),
            ),
        ],  # type: ignore
    )
    def test_angular_distributions(
        self,
        angular_variables: Union[str, Sequence[str]],
        expected_distribution_function: sy.Expr,
        sympy_model: sy.Expr,
    ) -> None:
        if isinstance(angular_variables, str):
            angular_variables = (angular_variables,)

        # remove angular variable
        integration_variable_set = set(angular_variables)
        integration_variables = [
            x
            for x in sympy_model.free_symbols
            if x.name not in integration_variable_set
        ]

        # Note: using nsimplify with rational=True solves assertion failure due
        # to float point imprecision
        assert normalize(
            expected_distribution_function, angular_variables
        ) == normalize(
            calculate_sympy_integral(
                sympy_model,
                integration_variables,
            ),
            angular_variables,
        )


class TestD1ToD0PiPi:
    @pytest.fixture(scope="class")
    def sympy_model(self) -> sy.Expr:
        result = es.generate_transitions(
            initial_state=[("D(1)(2420)0", [-1])],
            final_state=[("D0", [0]), ("pi-", [0]), ("pi+", [0])],
            allowed_intermediate_particles=["D*"],
            allowed_interaction_types="strong",
        )
        amplitude_model = es.amplitude.generate(result)

        amplitude_model.parameters[
            sy.Symbol(
                "C[D_{1}(2420)^{0} \\to D^{*}(2010)^{+}_{0} \\pi^{-}_{0};"
                "D^{*}(2010)^{+} \\to D^{0}_{0} \\pi^{+}_{0}]"
            )
        ].value = 0.5
        sympy_model = amplitude_model.expression
        sympy_model.dynamics = {
            k: 1.0 + sy.I * 0.0 for k in sympy_model.dynamics.keys()
        }
        # replace coefficients with 1
        full_model = sy.simplify(
            sympy_model.full_expression.subs(
                {
                    param: props.value
                    for param, props in amplitude_model.parameters.items()
                }
            )
            .doit()
            .expand(complex=True)
        )
        assert sy.im(full_model) == 0
        return sy.re(full_model)

    @pytest.mark.parametrize(
        "angular_variables, expected_distribution_function",  # type: ignore
        [
            (  # theta distribution from D1 decay
                "theta_0_1+2",
                sy.Rational(5, 4)
                + sy.Rational(3, 4)
                * sy.cos(sy.Symbol("theta_0_1+2", real=True)) ** 2,
            ),
            (  # theta distribution from D*
                "theta_1_2_vs_0",
                1
                - sy.Rational(3, 4)
                * sy.cos(sy.Symbol("theta_1_2_vs_0", real=True)) ** 2,
            ),
            (  # phi distribution of the D* decay
                "phi_1_2_vs_0",
                1
                - sy.Rational(4, 9)
                * sy.cos(2 * sy.Symbol("phi_1_2_vs_0", real=True)),
            ),
        ],  # type: ignore
    )
    def test_angular_distributions(
        self,
        angular_variables: Union[str, Sequence[str]],
        expected_distribution_function: sy.Expr,
        sympy_model: sy.Expr,
    ) -> None:
        if isinstance(angular_variables, str):
            angular_variables = (angular_variables,)

        # remove angular variable
        integration_variable_set = set(angular_variables)
        integration_variables = [
            x
            for x in sympy_model.free_symbols
            if x.name not in integration_variable_set
        ]

        # Note: using nsimplify with rational=True solves assertion failure due
        # to float point imprecision
        assert normalize(
            expected_distribution_function, angular_variables
        ) == normalize(
            calculate_sympy_integral(
                sympy_model,
                integration_variables,
            ),
            angular_variables,
        )
