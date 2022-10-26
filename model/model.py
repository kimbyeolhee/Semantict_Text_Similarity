from base import BaseModel
import torch.nn as nn
from transformers import AutoModelForSequenceClassification

class Roberta(BaseModel):
    def __init__(self, checkpoint, criterion, metrics, optimizer, lr_scheduler=None):
        super().__init__()
        self.save_hyperparameters()
        
        # pretrained model name or checkpoint
        self.checkpoint = checkpoint 

        # 사용할 모델을 호출합니다.
        self.lm = AutoModelForSequenceClassification.from_pretrained(
            pretrained_model_name_or_path=checkpoint, num_labels=1
        )

        # Loss 계산을 위해 사용될 L1Loss를 호출합니다.
        self.criterion = criterion

        # metrics
        self.metric_fns = metrics

        # optimizer functions 
        self.optimizer = optimizer
        self.lr_scheduler = lr_scheduler

    def forward(self, x):
        x = self.lm(x)['logits']

        return x

    def training_step(self, batch, batch_idx):
        x, y = batch
        logits = self.forward(x)
        loss = self.criterion(logits, y.float())
        self.log("train_loss", loss)

        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        logits = self.forward(x)
        loss = self.criterion(logits, y.float())
        self.log("val_loss", loss)
        for metric_fn in self.metric_fns:
            self.log("val" + metric_fn.__name__, metric_fn(logits.squeeze(), y.squeeze()))

        return loss

    def test_step(self, batch, batch_idx):
        x, y = batch
        logits = self.forward(x)
        for metric_fn in self.metric_fns:
            self.log("test" + metric_fn.__name__, metric_fn(logits.squeeze(), y.squeeze()))

    def predict_step(self, batch, batch_idx):
        x = batch
        logits = self.forward(x)

        return logits.squeeze()

    def configure_optimizers(self):
        optimizer = self.optimizer(params=self.parameters())
        if self.lr_scheduler:
            lr_scheduler = self.lr_scheduler(optimizer=optimizer)
            return {
                "optimizer": optimizer,
                "lr_scheduler": lr_scheduler
            }
        else:
            return optimizer