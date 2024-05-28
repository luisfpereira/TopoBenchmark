"""Test the message passing module."""

import torch

from modules.data.utils.utils import load_manual_graph
from modules.transforms.liftings.graph2cell.neighborhood_lifting import (
    NeighborhoodLifting,
)


class TestCellCyclesLifting:
    """Test the NeighborhoodLifting class."""

    def setup_method(self):
        # Load the graph
        self.data = load_manual_graph()

        # Initialise the NeighborhoodLifting class
        self.lifting = NeighborhoodLifting()

    def test_lift_topology(self):
        # Test the lift_topology method
        lifted_data = self.lifting.forward(self.data.clone())

        U, S, V = torch.svd(lifted_data.incidence_1.to_dense())
        expected_incidence_1_singular_values = torch.tensor(
            [3.4431, 2.4495, 2.4495, 2.3984, 2.2361, 2.2050, 1.9275, 1.6779]
        )

        assert (
            expected_incidence_1_singular_values == S
        ).all(), "Something is wrong with incidence_1."

        U, S, V = torch.svd(lifted_data.incidence_2.to_dense())
        expected_incidence_2_singular_values = torch.tensor(
            [3.8155, 3.0758, 2.5256, 2.3475, 1.8136, 1.5562, 1.3854, 1.2090]
        )

        assert (
            expected_incidence_2_singular_values == S
        ).all(), "Something is wrong with incidence_2."
