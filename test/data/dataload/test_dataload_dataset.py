import torch
from torch_geometric.data import Data 
from topobenchmarkx.data.dataload import DataloadDataset

class TestDataloadDataset:

    def setup_method(self):
        self.data_list = [
            Data(x=torch.randn(4, 6), edge_index=torch.randint(0, 4, (2, 4))),
            Data(x=torch.randn(3, 6), edge_index=torch.randint(0, 3, (2, 3)), x_1=torch.randn(5, 6)),
        ]
        self.dataset = DataloadDataset(self.data_list)

    def test_len(self):
        assert len(self.dataset) == 2

    def test_get(self):
        for i in range(len(self.data_list)):
            data, keys = self.dataset.get(i)

            expected_keys = list(self.data_list[i].keys())
            expected_data = [self.data_list[i][key] for key in expected_keys]

            assert keys == expected_keys
        
        for d, expected in zip(data, expected_data):
            assert torch.equal(d, expected)