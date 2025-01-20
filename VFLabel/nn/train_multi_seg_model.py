import os

import dataset
import lr_scheduler
import segmentation_models_pytorch as smp
import torch
import torch.nn as nn
import torch.optim as optim
import torchmetrics
import torchmetrics.detection
from torch.utils.data import DataLoader

from VFLabel.utils.defines import NN_MODE

# TODO: Pass device along in functions instead of defining it globally
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def train_point_predictor_network(project_path: str) -> nn.Module:
    checkpoint_path = os.path.join(project_path, "unet_point_predictor.pth.tar")

    # TODO: Decide if we should load this from a JSON file.
    # Up until then, i'll hardcode stuff that has worked good for me in the past.
    batch_size: int = 8
    num_epochs: int = 100
    learning_rate: float = 0.0001
    encoder: str = "mobilenet_v2"

    train_ds = dataset.HaselDataset(project_path, NN_MODE.TRAIN)
    eval_ds = dataset.HaselDataset(project_path, NN_MODE.EVAL)

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        num_workers=4,
        pin_memory=True,
        shuffle=True,
        drop_last=True,
    )
    val_loader = DataLoader(
        eval_ds,
        batch_size=batch_size,
        num_workers=4,
        pin_memory=True,
        shuffle=False,
        drop_last=True,
    )

    model = smp.Unet(
        encoder_name=encoder,  # choose encoder, e.g. mobilenet_v2 or efficientnet-b7
        encoder_weights="imagenet",  # use `imagenet` pre-trained weights for encoder initialization
        in_channels=1,  # model input channels (1 for gray-scale images, 3 for RGB, etc.)
        classes=1,
    )

    loss_func = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(
        model.decoder.parameters(),
        lr=learning_rate,
    )

    best_iou = 0.0
    scheduler = lr_scheduler.PolynomialLR(optimizer, num_epochs, power=0.99)
    for epoch in range(num_epochs):
        scheduler.update_lr()

        # Train the network
        train_loss = train(train_loader, loss_func, model, scheduler)

        # Eval
        eval_dice, eval_iou, eval_loss = evaluate(val_loader, model, loss_func)

        if eval_iou.item() > best_iou:
            state_dict = model.state_dict().cpu()
            checkpoint = {"optimizer": optimizer.state_dict()} | state_dict
            torch.save(checkpoint, checkpoint_path)
            best_iou = eval_iou

    del model

    best_model = smp.Unet(
        encoder_name=encoder,  # choose encoder, e.g. mobilenet_v2 or efficientnet-b7
        encoder_weights="imagenet",  # use `imagenet` pre-trained weights for encoder initialization
        in_channels=1,  # model input channels (1 for gray-scale images, 3 for RGB, etc.)
        classes=1,
    ).cpu()
    best_model = model.load_state_dict(state_dict)
    return best_model


def train(train_loader, loss_func, model, scheduler):
    model.train()
    running_average = 0.0
    count = 0
    for images, gt_seg in train_loader:
        if images.shape[0] != 8:
            continue

        scheduler.zero_grad()

        images = images.to(device=DEVICE)
        gt_seg = gt_seg.to(device=DEVICE)

        # forward
        pred_seg = model(images).squeeze()
        loss = loss_func(pred_seg.float(), gt_seg.float())

        loss.backward()
        scheduler.step()

        running_average += loss.item()
        count += images.shape[0]

    return running_average / count


def evaluate(val_loader, model, loss_func):
    running_average = 0.0
    count = 0

    model.eval()

    dice = torchmetrics.F1Score(task="binary")
    iou = torchmetrics.JaccardIndex(task="binary")

    for images, gt_seg in val_loader:
        if images.shape[0] != 8:
            continue

        images = images.to(device=DEVICE)
        gt_seg = gt_seg.long().to(device=DEVICE)

        pred_seg = model(images).squeeze()
        softmax = pred_seg.softmax(dim=1).detach()
        dice(softmax.cpu(), gt_seg.cpu())
        iou(softmax.cpu(), gt_seg.cpu())

        loss = loss_func(pred_seg.detach(), gt_seg.float()).item()
        running_average += loss
        count += images.shape[0]

    dice_score = dice.compute()
    iou_score = iou.compute()

    print("DICE: {0:03f}, IoU: {1:03f}".format(dice_score, iou_score))

    return dice_score, iou_score, running_average / count
