# pylint: disable=no-member,no-self-use
import numpy as np
import pytest

from expertsystem.amplitude.data import LorentzVector, MomentumPool


class TestLorentzVector:
    def test_properties(self):
        sample = np.array([[0, 1, 2, 3]]).view(LorentzVector)
        assert len(sample) == 1
        assert sample.shape == (1, 4)
        assert sample.energy == 0
        assert sample.p_x == 1
        assert sample.p_y == 2
        assert sample.p_z == 3
        assert sample.three_momentum.tolist() == [[1, 2, 3]]
        assert sample.p[0] == [np.sqrt(1 ** 2 + 2 ** 2 + 3 ** 2)]

    @pytest.mark.parametrize(
        "state_id, expected_mass",
        [
            (0, 0.13498),
            (1, 0.00048 + 0.00032j),
            (2, 0.13498),
            (3, 0.13498),
        ],
    )
    def test_mass(
        self,
        data_sample: MomentumPool,
        state_id: int,
        expected_mass: float,
    ):
        four_momenta = data_sample[state_id]
        n_events = 10
        assert four_momenta.shape == (n_events, 4)
        inv_mass = data_sample[state_id].mass()
        assert inv_mass.shape == (n_events,)
        average_mass = np.average(inv_mass)
        assert pytest.approx(average_mass, abs=1e-5) == expected_mass

    def test_phi(self):
        vector = np.array([[0, 1, 1, 0]]).view(LorentzVector)
        assert pytest.approx(vector.phi()) == np.pi / 4

    def test_theta(self):
        vector = np.array([[0, 0, 1, 1]]).view(LorentzVector)
        assert pytest.approx(vector.theta()) == np.pi / 4
        vector = np.array([[0, 1, 0, 1]]).view(LorentzVector)
        assert pytest.approx(vector.theta()) == np.pi / 4
