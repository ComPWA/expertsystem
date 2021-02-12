# cspell:ignore Asner Nakamura
# pylint: disable=invalid-name

"""Lineshape functions that describe the dynamics.

.. seealso:: :doc:`/usage/dynamics`
"""

import sympy as sy


def blatt_weisskopf(
    q: sy.Symbol, d: sy.Symbol, angular_momentum: sy.Symbol
) -> sy.Expr:
    r"""Blatt-Weisskopf function (:math:`B_L`), up to :math:`L \leq 4`.

    Each of these cases has been taken from
    :cite:`chungPartialWaveAnalysis1995`, p. 415. For a good overview of where
    to use these Blatt-Weisskopf functions, see
    :cite:`asnerDalitzPlotAnalysis2006`.

    .. glue:math:: blatt_weisskopf
        :label: blatt_weisskopf

    See :ref:`usage/dynamics:_With_ form factor`.
    """
    z = (q * d) ** 2
    return sy.Piecewise(
        (
            1,
            sy.Eq(angular_momentum, 0),
        ),
        (
            sy.sqrt(2 * z / (z + 1)),
            sy.Eq(angular_momentum, 1),
        ),
        (
            sy.sqrt(13 * z ** 2 / ((z - 3) * (z - 3) + 9 * z)),
            sy.Eq(angular_momentum, 2),
        ),
        (
            sy.sqrt(
                277
                * z ** 3
                / (z * (z - 15) * (z - 15) + 9 * (2 * z - 5) * (2 * z - 5))
            ),
            sy.Eq(angular_momentum, 3),
        ),
        (
            sy.sqrt(
                12746
                * z ** 4
                / (
                    (z ** 2 - 45 * z + 105) * (z ** 2 - 45 * z + 105)
                    + 25 * z * (2 * z - 21) * (2 * z - 21)
                )
            ),
            sy.Eq(angular_momentum, 4),
        ),
    )


def relativistic_breit_wigner(
    mass: sy.Symbol, mass0: sy.Symbol, gamma0: sy.Symbol
) -> sy.Expr:
    """Relativistic Breit-Wigner lineshape.

    .. glue:math:: relativistic_breit_wigner
        :label: relativistic_breit_wigner

    See :ref:`usage/dynamics:_Without_ form factor` and
    :cite:`asnerDalitzPlotAnalysis2006`.
    """
    return gamma0 * mass0 / (mass0 ** 2 - mass ** 2 - gamma0 * mass0 * sy.I)


def relativistic_breit_wigner_with_ff(  # pylint: disable=too-many-arguments
    mass: sy.Symbol,
    mass0: sy.Symbol,
    gamma0: sy.Symbol,
    m_a: sy.Symbol,
    m_b: sy.Symbol,
    angular_momentum: sy.Symbol,
    meson_radius: sy.Symbol,
) -> sy.Expr:
    """Relativistic Breit-Wigner with `.BlattWeisskopf` factor.

    For :math:`l=0`, this lineshape has the following form:

    .. glue:math:: relativistic_breit_wigner_with_ff
        :label: relativistic_breit_wigner_with_ff

    See :ref:`usage/dynamics:_With_ form factor` and
    :cite:`asnerDalitzPlotAnalysis2006`.
    """
    q = breakup_momentum(mass, m_a, m_b)
    q0 = breakup_momentum(mass0, m_a, m_b)
    ff = blatt_weisskopf(q, meson_radius, angular_momentum)
    ff0 = blatt_weisskopf(q0, meson_radius, angular_momentum)
    width = gamma0 * (mass0 / mass) * (ff ** 2 / ff0 ** 2)
    width = width * (q / q0)
    return relativistic_breit_wigner(mass, mass0, width) * ff


def breakup_momentum(
    m_r: sy.Symbol, m_a: sy.Symbol, m_b: sy.Symbol
) -> sy.Expr:
    return sy.sqrt(
        (m_r ** 2 - (m_a + m_b) ** 2)
        * (m_r ** 2 - (m_a - m_b) ** 2)
        / (4 * m_r ** 2)
    )
