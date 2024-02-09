from typing import Any, Dict, Tuple

import torch
from lightning import LightningModule
from torchmetrics import MaxMetric, MeanMetric
from torchmetrics.classification.accuracy import Accuracy

from topobenchmarkx.models.wrappers.default_wrapper import HypergraphWrapper, SANWrapper

# import topomodelx


class NetworkModule(LightningModule):
    """Example of a `LightningModule` for MNIST classification.

    A `LightningModule` implements 8 key methods:



    Docs:
        https://lightning.ai/docs/pytorch/latest/common/lightning_module.html
    """

    def __init__(
        self,
        backbone: torch.nn.Module,
        readout_workaround: torch.nn.Module,
        readout: torch.nn.Module,
        loss: torch.nn.Module,
        optimizer: torch.optim.Optimizer,
        scheduler: torch.optim.lr_scheduler,
        compile: bool,
    ) -> None:
        """Initialize a `NetworkModule`.

        :param backbone: The backbone model to train.
        :param readout: The readout class.
        :param loss: The loss class.
        :param optimizer: The optimizer to use for training.
        :param scheduler: The learning rate scheduler to use for training.
        """
        super().__init__()

        # this line allows to access init params with 'self.hparams' attribute
        # also ensures init params will be stored in ckpt
        self.save_hyperparameters(logger=False)

        if str(backbone.__class__) in [
            "<class 'topomodelx.nn.hypergraph.unigcnii.UniGCNII'>",
            "<class 'topomodelx.nn.hypergraph.allset_transformer.AllSetTransformer'>",
        ]:
            self.backbone = HypergraphWrapper(backbone)

        elif str(backbone.__class__) in ["<class 'topomodelx.nn.simplicial.san.SAN'>"]:
            self.backbone = SANWrapper(backbone)
        else:
            raise NotImplementedError(f"Backbone {backbone.__class__} not implemented")

        self.readout_workaround = readout_workaround
        self.readout = readout
        self.evaluator = None

        # loss function
        self.criterion = loss

        # for tracking best so far validation accuracy
        self.val_acc_best = MaxMetric()

    def forward(self, batch) -> dict:
        """Perform a forward pass through the model `self.backbone`.

        :param x: A tensor of images.
        :return: A tensor of logits.
        """
        return self.backbone(batch)  # self.backbone(x, edge_index)

    def on_train_start(self) -> None:
        """Lightning hook that is called when training begins."""
        # by default lightning executes validation step sanity checks before training starts,
        # so it's worth to make sure validation metrics don't store results from these checks
        # self.val_loss.reset()
        # self.val_acc.reset()
        self.val_acc_best.reset()

    def model_step(self, batch) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Perform a single model step on a batch of data.

        :param batch: A batch of data (a tuple) containing the input tensor of images and target labels.

        :return: A tuple containing (in order):
            - A tensor of losses.
            - A tensor of predictions.
            - A tensor of target labels.
        """
        # model_out = {"labels": batch.y}
        # x_0, x_1 = self.forward(batch.x, batch.edge_index)
        # model_out["x_0"] = x_0
        # model_out["hyperedge"] = x_1
        model_out = self.forward(batch)
        model_out = self.readout(model_out)
        model_out = self.criterion(model_out)

        return model_out

    def training_step(self, batch, batch_idx: int) -> torch.Tensor:
        """Perform a single training step on a batch of data from the training set.

        :param batch: A batch of data (a tuple) containing the input tensor of images and target
            labels.
        :param batch_idx: The index of the current batch.
        :return: A tensor of losses between model predictions and targets.
        """
        # if data_transform == True:
        #     batch = data_transform(batch)

        model_out = self.model_step(batch)

        # Keep only train data points
        for key, val in model_out.items():
            if key not in ["loss", "hyperedge"]:
                model_out[key] = val[batch.train_mask]
        # Criterion
        self.criterion(model_out)

        # Evaluation
        self.evaluator.eval(model_out)

        # update and log metrics
        # self.train_acc(model_out["logits"].argmax(1), model_out["labels"])
        self.log(
            "train/loss", model_out["loss"], on_step=False, on_epoch=True, prog_bar=True
        )

        for key in model_out["metrics"].keys():
            self.log(
                f"train/{key}",
                model_out["metrics"][key],
                on_step=False,
                on_epoch=True,
                prog_bar=True,
            )

        # return loss or backpropagation will fail
        return model_out["loss"]

    def on_train_epoch_end(self) -> None:
        "Lightning hook that is called when a training epoch ends."
        pass

    def validation_step(
        self, batch: Tuple[torch.Tensor, torch.Tensor], batch_idx: int
    ) -> None:
        """Perform a single validation step on a batch of data from the validation set.

        :param batch: A batch of data (a tuple) containing the input tensor of images and target
            labels.
        :param batch_idx: The index of the current batch.
        """
        model_out = self.model_step(batch)

        # Keep only train data points
        for key, val in model_out.items():
            if key not in ["loss", "hyperedge"]:
                model_out[key] = val[batch.val_mask]

        # update and log metrics
        self.criterion(model_out)

        # Evaluation
        self.evaluator.eval(model_out)

        self.log(
            "val/loss", model_out["loss"], on_step=False, on_epoch=True, prog_bar=True
        )

        for key in model_out["metrics"].keys():
            self.log(
                f"val/{key}",
                model_out["metrics"][key],
                on_step=False,
                on_epoch=True,
                prog_bar=True,
            )

        # To track best so far validation accuracy (to be changed in future)
        self.val_acc_best(model_out["metrics"]["acc"])
        # self.log("val/acc", self.val_acc, on_step=False, on_epoch=True, prog_bar=True)

    def on_validation_epoch_end(self) -> None:
        "Lightning hook that is called when a validation epoch ends."
        # acc = self.val_acc.compute()  # get current val acc
        # self.val_acc_best(acc)  # update best so far val acc

        # log `val_acc_best` as a value through `.compute()` method, instead of as a metric object
        # otherwise metric would be reset by lightning after each epoch

        self.log(
            "val/acc_best", self.val_acc_best.compute(), sync_dist=True, prog_bar=True
        )

    def test_step(
        self, batch: Tuple[torch.Tensor, torch.Tensor], batch_idx: int
    ) -> None:
        """Perform a single test step on a batch of data from the test set.

        :param batch: A batch of data (a tuple) containing the input tensor of images and target
            labels.
        :param batch_idx: The index of the current batch.
        """

        model_out = self.model_step(batch)

        # Keep only train data points
        for key, val in model_out.items():
            if key not in ["loss", "hyperedge"]:
                model_out[key] = val[batch.test_mask]

        self.criterion(model_out)

        # Evaluation
        self.evaluator.eval(model_out)

        # update and log metrics
        # self.test_loss(loss)
        # self.test_acc(model_out["logits"].argmax(1), model_out["labels"])
        self.log(
            "test/loss", model_out["loss"], on_step=False, on_epoch=True, prog_bar=True
        )
        for key in model_out["metrics"].keys():
            self.log(
                f"test/{key}",
                model_out["metrics"][key],
                on_step=False,
                on_epoch=True,
                prog_bar=True,
            )
        # self.log("test/acc", self.test_acc, on_step=False, on_epoch=True, prog_bar=True)

    def on_test_epoch_end(self) -> None:
        """Lightning hook that is called when a test epoch ends."""
        pass

    def setup(self, stage: str) -> None:
        """Lightning hook that is called at the beginning of fit (train + validate), validate,
        test, or predict.

        This is a good hook when you need to build models dynamically or adjust something about
        them. This hook is called on every process when using DDP.

        :param stage: Either `"fit"`, `"validate"`, `"test"`, or `"predict"`.
        """
        if self.hparams.compile and stage == "fit":
            self.net = torch.compile(self.net)

    def configure_optimizers(self) -> Dict[str, Any]:
        """Choose what optimizers and learning-rate schedulers to use in your optimization.
        Normally you'd need one. But in the case of GANs or similar you might have multiple.

        Examples:
            https://lightning.ai/docs/pytorch/latest/common/lightning_module.html#configure-optimizers

        :return: A dict containing the configured optimizers and learning-rate schedulers to be used for training.
        """
        optimizer = self.hparams.optimizer(
            params=list(self.trainer.model.parameters())
            + list(self.readout.parameters())
        )
        if self.hparams.scheduler is not None:
            scheduler = self.hparams.scheduler(optimizer=optimizer)
            return {
                "optimizer": optimizer,
                "lr_scheduler": {
                    "scheduler": scheduler,
                    "monitor": "val/loss",
                    "interval": "epoch",
                    "frequency": 1,
                },
            }
        return {"optimizer": optimizer}


# self.criterion = torch.nn.CrossEntropyLoss()

# self.evaluator = evaluator
# # metric objects for calculating and averaging accuracy across batches
# self.train_acc = Accuracy(task="multiclass", num_classes=7)
# self.val_acc = Accuracy(task="multiclass", num_classes=7)
# self.test_acc = Accuracy(task="multiclass", num_classes=7)

# for averaging loss across batches
# self.train_loss = MeanMetric()
# self.val_loss = MeanMetric()
# self.test_loss = MeanMetric()

if __name__ == "__main__":
    _ = NetworkModule(None, None, None, None)
