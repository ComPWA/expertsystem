# cspell:ignore nsimplify
# pylint: disable=redefined-outer-name,no-self-use

from typing import Any, List, Optional, Sequence, Union

import pytest
import sympy as sp

import expertsystem as es
from expertsystem.reaction.particle import ParticleCollection


def calculate_sympy_integral(
    intensity: Any,
    integration_variables: List[sp.Symbol],
    jacobi_determinant: Optional[Any] = None,
) -> sp.Expr:
    if jacobi_determinant is None:
        for int_var in integration_variables:
            if "theta" in int_var.name:
                intensity *= sp.sin(int_var)
    else:
        intensity *= jacobi_determinant
    return sp.trigsimp(
        sp.nsimplify(
            sp.re(
                sp.integrate(
                    intensity,
                    *(
                        (x, -sp.pi, sp.pi)
                        if "phi" in x.name
                        else (x, 0, sp.pi)
                        for x in integration_variables
                    ),
                )
            ).doit(),
            rational=True,
        )
    )


def normalize(
    sympy_expression: sp.Expr, variable_names: Sequence[str]
) -> sp.Expr:
    variables = [sp.Symbol(x, real=True) for x in variable_names]
    normalization = sp.integrate(
        sympy_expression,
        *(
            (x, -sp.pi, sp.pi) if "phi" in x.name else (x, 0, sp.pi)
            for x in variables
        ),
    )
    return sp.trigsimp((sympy_expression / normalization).expand(trig=True))


class TestEpemToDmD0Pip:
    @pytest.fixture(scope="class")
    def sympy_model(self, particle_database: ParticleCollection) -> sp.Expr:
        epem = es.reaction.particle.Particle(
            name="EpEm",
            pid=12345678,
            mass=4.36,
            spin=1.0,
            parity=es.reaction.particle.Parity(-1),
            c_parity=es.reaction.particle.Parity(-1),
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

        amplitude_model = es.amplitude.get_builder(result).generate()
        full_model = sp.simplify(
            amplitude_model.expression.subs(amplitude_model.parameter_defaults)
            .doit()
            .expand(complex=True)
        )
        assert sp.im(full_model) == 0
        return sp.re(full_model)

    @pytest.mark.parametrize(
        ("angular_variables", "expected_distribution_function"),
        [
            (  # cos(theta) distribution from epem decay
                "theta_1+2",
                1 + sp.cos(sp.Symbol("theta_1+2", real=True)) ** 2,
            ),
            (  # phi distribution of the epem decay
                "phi_1+2",
                1,
            ),
            (  # cos(theta') distribution from D2*
                "theta_1,1+2",
                1
                - (2 * sp.cos(sp.Symbol("theta_1,1+2", real=True)) ** 2 - 1)
                ** 2,
            ),
            (  # phi' distribution of the D2* decay
                "phi_1,1+2",
                3 - 2 * sp.sin(sp.Symbol("phi_1,1+2", real=True)) ** 2,
            ),
            (  # 2d distribution of the D2* decay
                ["theta_1,1+2", "phi_1,1+2"],
                (1 - sp.cos(sp.Symbol("theta_1,1+2", real=True)) ** 2)
                * (sp.cos(sp.Symbol("theta_1,1+2", real=True)) ** 2)
                * (2 + sp.cos(2 * sp.Symbol("phi_1,1+2", real=True))),
            ),
        ],  # type: ignore
    )
    def test_angular_distributions(
        self,
        angular_variables: Union[str, Sequence[str]],
        expected_distribution_function: sp.Expr,
        sympy_model: sp.Expr,
    ) -> None:
        assert {s.name for s in sympy_model.free_symbols} == {
            "phi_1,1+2",
            "theta_1+2",
            "theta_1,1+2",
        }

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
    def sympy_model(self) -> sp.Expr:
        result = es.generate_transitions(
            initial_state=[("D(1)(2420)0", [-1])],
            final_state=[("D0", [0]), ("pi-", [0]), ("pi+", [0])],
            allowed_intermediate_particles=["D*"],
            allowed_interaction_types="strong",
        )
        amplitude_model = es.amplitude.get_builder(result).generate()

        amplitude_model.parameter_defaults[
            sp.Symbol(
                "C[D_{1}(2420)^{0} \\to D^{*}(2010)^{+}_{0} \\pi^{-}_{0};"
                "D^{*}(2010)^{+} \\to D^{0}_{0} \\pi^{+}_{0}]"
            )
        ] = 0.5

        full_model = sp.simplify(
            amplitude_model.expression.subs(amplitude_model.parameter_defaults)
            .doit()
            .expand(complex=True)
        )
        assert sp.im(full_model) == 0
        return sp.re(full_model)

    @pytest.mark.parametrize(
        ("angular_variables", "expected_distribution_function"),
        [
            (  # theta distribution from D1 decay
                "theta_1+2",
                sp.Rational(5, 4)
                + sp.Rational(3, 4)
                * sp.cos(sp.Symbol("theta_1+2", real=True)) ** 2,
            ),
            (  # theta distribution from D*
                "theta_1,1+2",
                1
                - sp.Rational(3, 4)
                * sp.cos(sp.Symbol("theta_1,1+2", real=True)) ** 2,
            ),
            (  # phi distribution of the D* decay
                "phi_1,1+2",
                1
                - sp.Rational(4, 9)
                * sp.cos(2 * sp.Symbol("phi_1,1+2", real=True)),
            ),
        ],  # type: ignore
    )
    def test_angular_distributions(
        self,
        angular_variables: Union[str, Sequence[str]],
        expected_distribution_function: sp.Expr,
        sympy_model: sp.Expr,
    ) -> None:
        assert {s.name for s in sympy_model.free_symbols} == {
            "phi_1,1+2",
            "theta_1+2",
            "theta_1,1+2",
        }

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
