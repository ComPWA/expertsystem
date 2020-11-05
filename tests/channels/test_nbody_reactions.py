# pylint: disable=redefined-outer-name
from typing import Set, Tuple

import pytest

from expertsystem.reaction import check_reaction_violations


def reduce_violated_rules(violated_rules: Set[Tuple[str, ...]]) -> Set[str]:
    reduced_violations = set()
    for rule_group in violated_rules:
        reduced_violations.update(set(x for x in rule_group))

    return reduced_violations


@pytest.mark.slow
@pytest.mark.parametrize(
    "test_input, expected",
    [
        (
            (["p", "p~"], ["pi+", "pi0"]),
            ["ChargeConservation", "isospin_conservation"],
        ),
        ((["eta"], ["gamma", "gamma"]), []),
        (
            (["Sigma0"], ["Lambda", "pi0"]),
            ["MassConservation"],
        ),
        (
            (["Sigma-"], ["n", "pi-"]),
            [
                "isospin_conservation",
                "StrangenessConservation",
            ],
        ),
        ((["e+", "e-"], ["mu+", "mu-"]), []),
        (
            (["mu-"], ["e-", "nu(e)~"]),
            ["MuonLNConservation", "spin_magnitude_conservation"],
        ),
        (
            (["mu-"], ["e-", "nu(e)"]),
            [
                "ElectronLNConservation",
                "MuonLNConservation",
                "spin_magnitude_conservation",
            ],
        ),
        ((["Delta(1232)+"], ["p", "pi0"]), []),
        ((["nu(e)~", "p"], ["n", "e+"]), []),
        (
            (["e-", "p"], ["nu(e)", "pi0"]),
            ["BaryonNumberConservation", "spin_magnitude_conservation"],
        ),
        ((["f(0)(980)"], ["pi+", "pi-"]), []),
        ((["pi0"], ["gamma", "gamma"]), []),
        (
            (["pi0"], ["gamma", "gamma", "gamma"]),
            ["c_parity_conservation"],
        ),
        ((["pi0"], ["e+", "e-", "gamma"]), []),
        ((["pi0"], ["e+", "e-"]), []),
        (
            (["J/psi(1S)"], ["pi0", "f(0)(980)"]),
            ["isospin_conservation", "c_parity_conservation"],
        ),
        ((["p", "p"], ["Sigma+", "n", "K0", "pi+", "pi0"]), []),
        (
            (["p", "p"], ["Sigma+", "n", "K~0", "pi+", "pi0"]),
            ["StrangenessConservation", "isospin_conservation"],
        ),
        (
            (["p"], ["e+", "gamma"]),
            ["ElectronLNConservation", "BaryonNumberConservation"],
        ),
        ((["p", "p"], ["p", "p", "p", "p~"]), []),
        ((["n", "n~"], ["pi+", "pi-", "pi0"]), []),
        (
            (["pi+", "n"], ["pi-", "p"]),
            ["ChargeConservation", "isospin_conservation"],
        ),
        (
            (["K-"], ["pi-", "pi0"]),
            ["isospin_conservation", "StrangenessConservation"],
        ),
        (
            (["Sigma+", "n"], ["Sigma-", "p"]),
            ["ChargeConservation", "isospin_conservation"],
        ),
        ((["Sigma0"], ["Lambda", "gamma"]), []),
        (
            (["Xi-"], ["Lambda", "pi-"]),
            ["StrangenessConservation", "isospin_conservation"],
        ),
        (
            (["Xi0"], ["p", "pi-"]),
            ["StrangenessConservation", "isospin_conservation"],
        ),
        ((["pi-", "p"], ["Lambda", "K0"]), []),
        ((["pi0"], ["gamma", "gamma"]), []),
        ((["pi0"], ["gamma", "gamma", "gamma"]), ["c_parity_conservation"]),
        ((["Sigma-"], ["n", "e-", "nu(e)~"]), ["StrangenessConservation"]),
        (
            (["rho(770)0"], ["pi0", "pi0"]),
            [
                "isospin_conservation",  # Clebsch Gordan coefficient = 0
                "c_parity_conservation",
                "identical_particle_symmetrization",
            ],
        ),
        ((["rho(770)0"], ["gamma", "gamma"]), ["c_parity_conservation"]),
        ((["rho(770)0"], ["gamma", "gamma", "gamma"]), []),
        (
            (["J/psi(1S)"], ["pi0", "eta"]),
            ["c_parity_conservation", "isospin_conservation"],
        ),
        (
            (["J/psi(1S)"], ["rho(770)0", "rho(770)0"]),
            ["c_parity_conservation", "g_parity_conservation"],
        ),
        (
            (["K~0"], ["pi+", "pi-", "pi0"]),
            ["isospin_conservation", "StrangenessConservation"],
        ),
    ],
)
def test_nbody_reaction(test_input, expected):
    # define all of the different decay scenarios
    print("processing case:" + str(test_input))

    violations = check_reaction_violations(
        initial_state=test_input[0],
        final_state=test_input[1],
    )

    reduced_violations = reduce_violated_rules(violations)
    print("not allowed! violates: " + str(reduced_violations))
    assert reduced_violations == set(expected)
