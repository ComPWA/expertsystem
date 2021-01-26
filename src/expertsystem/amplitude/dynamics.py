"""Lineshape functions that describe the dynamics."""

import sympy as sy


def hankel1(angular_momentum: sy.Symbol, x: sy.Symbol) -> sy.Expr:
    x_squared = x ** 2
    return sy.Piecewise(
        (
            1,
            sy.Eq(angular_momentum, 0),
        ),
        (
            1 + x_squared,
            sy.Eq(angular_momentum, 1),
        ),
        (
            9 + x_squared * (3 + x_squared),
            sy.Eq(angular_momentum, 2),
        ),
        (
            225 + x_squared * (45 + x_squared * (6 + x_squared)),
            sy.Eq(angular_momentum, 3),
        ),
        (
            1575 + x_squared * (135 + x_squared * (10 + x_squared)),
            sy.Eq(angular_momentum, 4),
        ),
    )


def blatt_weisskopf(
    q: sy.Symbol, q_r: sy.Symbol, angular_momentum: sy.Symbol
) -> sy.Expr:
    return sy.sqrt(
        abs(hankel1(angular_momentum, q)) ** 2
        / abs(hankel1(angular_momentum, q_r)) ** 2
    )


def relativistic_breit_wigner(
    mass: sy.Symbol, mass0: sy.Symbol, gamma0: sy.Symbol
) -> sy.Expr:
    return gamma0 / (mass0 ** 2 - mass ** 2 - gamma0 * mass0 * sy.I)


def relativistic_breit_wigner_with_form_factor(  # pylint: disable=too-many-arguments
    mass: sy.Symbol,
    mass0: sy.Symbol,
    gamma0: sy.Symbol,
    m_a: sy.Symbol,
    m_b: sy.Symbol,
    angular_momentum: sy.Symbol,
    meson_radius: sy.Symbol,
) -> sy.Expr:
    q_squared = two_body_momentum_squared(mass, m_a, m_b)
    q0_squared = two_body_momentum_squared(mass0, m_a, m_b)
    ff2 = blatt_weisskopf(q_squared, meson_radius, angular_momentum)
    ff02 = blatt_weisskopf(q0_squared, meson_radius, angular_momentum)
    width = gamma0 * (mass0 / mass) * (ff2 / ff02)
    width = width * sy.sqrt(q_squared / q0_squared)
    return (
        relativistic_breit_wigner(mass, mass0, width)
        * mass0
        * gamma0
        * sy.sqrt(ff2)
    )


def two_body_momentum_squared(
    m_d: sy.Symbol, m_a: sy.Symbol, m_b: sy.Symbol
) -> sy.Expr:
    return (
        (m_d ** 2 - (m_a + m_b) ** 2)
        * (m_d ** 2 - (m_a - m_b) ** 2)
        / (4 * m_d ** 2)
    )
