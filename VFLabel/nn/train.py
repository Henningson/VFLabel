import torch
import albumentations as A
from albumentations.pytorch import ToTensorV2
from tqdm import tqdm
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt
import torch.nn.functional as F
from VFLabel.io.dataset import HLEDataset, ReinhardDatasetV2
from torch.utils.data import DataLoader
from VFLabel.nn.UNet import Model
from VFLabel.utils.LSQ import LSQLocalization
from VFLabel.utils.utils import (
    class_to_color,
    load_checkpoint,
    save_checkpoint,
    check_accuracy,
    save_predictions_as_imgs,
    draw_points,
    draw_heatmap,
)
import VFLabel.utils.Visualizer as Visualizer
import os

# Hyperparameters etc.
LEARNING_RATE = 1e-5
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
BATCH_SIZE = 1
NUM_EPOCHS = 50
NUM_WORKERS = 2
IMAGE_HEIGHT = 1200  # 1280 originally
IMAGE_WIDTH = 800  # 1918 originally
PIN_MEMORY = True
LOAD_MODEL = False
DATASET_BASE_DIR = "Dataset/"

DATASET_FOLDERS = []
for entry in os.listdir(DATASET_BASE_DIR):
    if not os.path.isdir(os.path.join(DATASET_BASE_DIR, entry)):
        continue

    DATASET_FOLDERS.append(entry)


def main():
    train_transform = A.Compose(
        [
            A.Resize(height=IMAGE_HEIGHT, width=IMAGE_WIDTH),
            A.Rotate(limit=35, p=1.0),
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.1),
            A.Normalize(
                mean=[0.0],
                std=[1.0],
                max_pixel_value=255.0,
            ),
            ToTensorV2(),
        ]
    )

    val_transforms = A.Compose(
        [
            A.Resize(height=IMAGE_HEIGHT, width=IMAGE_WIDTH),
            A.Normalize(
                mean=[0.0],
                std=[1.0],
                max_pixel_value=255.0,
            ),
            ToTensorV2(),
        ]
    )

    model = Model(
        in_channels=1, out_channels=2, features=[32, 64, 128, 256, 512, 1024]
    ).to(DEVICE)
    BCELoss = nn.CrossEntropyLoss()
    loc = LSQLocalization(local_maxima_window=21)

    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

    train_ds = ReinhardDatasetV2(
        base_path=DATASET_BASE_DIR,
        keys=DATASET_FOLDERS,
        transform=train_transform,
        is_train=True,
    )
    train_loader = DataLoader(
        train_ds,
        batch_size=BATCH_SIZE,
        num_workers=NUM_WORKERS,
        pin_memory=PIN_MEMORY,
        shuffle=True,
    )
    val_ds = ReinhardDatasetV2(
        base_path=DATASET_BASE_DIR,
        keys=DATASET_FOLDERS,
        transform=val_transforms,
        is_train=False,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=BATCH_SIZE,
        num_workers=NUM_WORKERS,
        pin_memory=PIN_MEMORY,
        shuffle=False,
    )

    # visual = Visualizer.Visualize2D(x=1)
    scaler = torch.cuda.amp.GradScaler()

    for epoch in range(NUM_EPOCHS):

        """
        if epoch % 5 == 0:
            with torch.no_grad():
                val_image, gt_seg = val_ds[0]

                pred_seg = model(val_image.unsqueeze(0).cuda())
                pred_seg = pred_seg.softmax(dim=1)
                _, mean, _ = loc.test(pred_seg)

                visual.draw_images(val_image.unsqueeze(0)*255)
                visual.draw_points(mean)
                visual.show()
                plt.show(block=True)
        """

        loop = tqdm(train_loader)
        for images, gt_seg in loop:
            images = images.to(device=DEVICE)
            gt_seg = gt_seg.to(device=DEVICE)

            # forward
            with torch.cuda.amp.autocast():
                segmentation = model(images)
                loss = BCELoss(segmentation.float(), gt_seg.long())

            optimizer.zero_grad()
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            # update tqdm loop
            loop.set_postfix(loss=loss.item())

        checkpoint = {
            "optimizer": optimizer.state_dict(),
        } | model.get_statedict()
        torch.save(checkpoint, "rhine_hard_net_large.pth.tar")


if __name__ == "__main__":
    main()