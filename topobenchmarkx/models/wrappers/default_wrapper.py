from abc import ABC, abstractmethod

import torch


class DefaultWrapper(ABC, torch.nn.Module):
    """Abstract class that provides an interface to loss logic within netowrk"""

    def __init__(self, backbone):
        super().__init__()
        self.backbone = backbone

    @abstractmethod
    def __call__(self, batch):
        """Define logic for forward pass"""
        pass


class HypergraphWrapper(DefaultWrapper):
    """Abstract class that provides an interface to loss logic within network"""

    def __init__(self, backbone):
        super().__init__(backbone)

    def __call__(self, batch):
        """Define logic for forward pass"""
        model_out = {"labels": batch.y}
        x_0, x_1 = self.backbone(batch.x, batch.incidence_1)
        model_out["x_0"] = x_0
        model_out["hyperedge"] = x_1
        return model_out


class SANWrapper(DefaultWrapper):
    """Abstract class that provides an interface to loss logic within network"""

    def __init__(self, backbone):
        super().__init__(backbone)

    def __call__(self, batch):
        """Define logic for forward pass"""
        model_out = {"labels": batch.y}

        x_1 = self.backbone(batch.x_1, batch.laplacian_up_1, batch.laplacian_down_1)
        # Project the edge-level output of the model back to the node-level
        x_0 = torch.sparse.mm(batch.incidence_1, x_1)
        model_out["x_0"] = x_0
        return model_out


class CANWrapper(DefaultWrapper):
    """Abstract class that provides an interface to loss logic within network"""

    def __init__(self, backbone):
        super().__init__(backbone)

    def __call__(self, batch):
        """Define logic for forward pass"""
        model_out = {"labels": batch.y}
        x_0 = self.backbone(
            batch.x,
            batch.x_1,
            batch.adjacency_0,
            batch.down_laplacian_1,
            batch.up_laplacian_1,
        )
        model_out["x_graph"] = x_0
        return model_out
