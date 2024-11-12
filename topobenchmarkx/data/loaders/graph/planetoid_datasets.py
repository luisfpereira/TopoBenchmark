"""Loaders for PLANETOID datasets."""

import os
from pathlib import Path
from typing import ClassVar

from omegaconf import DictConfig
from torch_geometric.data import Dataset
from torch_geometric.datasets import Planetoid

from topobenchmarkx.data.loaders.base import AbstractLoader


class PlanetoidDatasetLoader(AbstractLoader):
    """Load PLANETOID datasets.

    Parameters
    ----------
    parameters : DictConfig
        Configuration parameters containing:
            - data_dir: Root directory for data
            - data_name: Name of the dataset
            - data_type: Type of the dataset (e.g., "cocitation")
    """

    VALID_DATASETS: ClassVar[set[str]] = {"Cora", "citeseer", "PubMed"}
    VALID_TYPES: ClassVar[set[str]] = {"cocitation"}

    def __init__(self, parameters: DictConfig) -> None:
        super().__init__(parameters)
        self._validate_parameters()

    def _validate_parameters(self) -> None:
        """Validate the input parameters."""
        if self.parameters.data_name not in self.VALID_DATASETS:
            raise ValueError(
                f"Dataset '{self.parameters.data_name}' not supported. "
                f"Must be one of: {', '.join(sorted(self.VALID_DATASETS))}"
            )

        if self.parameters.data_type not in self.VALID_TYPES:
            raise ValueError(
                f"Data type '{self.parameters.data_type}' not supported. "
                f"Must be one of: {', '.join(sorted(self.VALID_TYPES))}"
            )

    def load_dataset(self) -> Dataset:
        """Load Planetoid dataset.

        Returns
        -------
        Dataset
            The loaded Planetoid dataset.

        Raises
        ------
        RuntimeError
            If dataset loading fails.
        """

        dataset = Planetoid(
            root=str(self.root_data_dir),
            name=self.parameters.data_name,
        )
        return dataset

    def get_data_dir(self) -> Path:
        """Get the data directory.

        Returns
        -------
        Path
            The path to the dataset directory.
        """
        return os.path.join(self.root_data_dir, self.parameters.data_name)
