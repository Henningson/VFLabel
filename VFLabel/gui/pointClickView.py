from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout


from PyQt5 import QtCore
import numpy as np

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QSlider,
    QPushButton,
    QLabel,
    QFileDialog,
    QComboBox,
    QMessageBox,
)

from PyQt5.QtGui import QIcon, QPen, QBrush, QPolygonF, QColor, QPixmap, QImage
import os

import VFLabel.utils.transforms

import VFLabel.gui.drawSegmentationWidget
import VFLabel.gui.transformSegmentationWidget
import VFLabel.gui.interpolateSegmentationWidget
import VFLabel.gui.videoPlayerWidget
import VFLabel.gui.videoViewWidget
import VFLabel.gui.zoomableViewWidget
import VFLabel.gui.videoOverlayWidget
import VFLabel.gui.buttonGridWidget

import VFLabel.utils.transforms
import VFLabel.io.data
import VFLabel.utils.utils
import json


from VFLabel.utils.defines import COLOR

from typing import List

##################### ^
#         #         # |
#         #         # |
#  GRID   #  VIDEO  # |
#         #         # |
#  DRAW   #         # |
#  REMOVE #         # |
##################### |
#  VWP    # SAVE    #


class PointClickView(QWidget):
    def __init__(
        self,
        grid_height: int,
        grid_width: int,
        video: np.array,
        project_path: str,
        parent=None,
    ):
        super(PointClickView, self).__init__(parent)
        self.project_path: str = project_path

        qvideo: List[QImage] = VFLabel.utils.transforms.vid_2_QImage(video)
        self.point_clicker_view = VFLabel.gui.pointClickWidget.PointClickWidget(
            qvideo, grid_height=grid_height, grid_width=grid_width
        )

        self.video_player = VFLabel.gui.videoPlayerWidget.VideoPlayerWidget(
            len(qvideo), 100
        )

        self.button_grid = VFLabel.gui.buttonGridWidget.ButtonGrid(
            grid_height=grid_height, grid_width=grid_width
        )
        self.button_draw = QPushButton("Add Points")
        self.button_remove = QPushButton("Remove Points")
        self.button_disable_modes = QPushButton("Disable Modes")

        self.save_button = QPushButton("Save")

        # Layouting, signals etc
        vertical_layout = QVBoxLayout()
        horizontal_layout_top = QHBoxLayout()
        top_widget = QWidget()
        horizontal_layout_bot = QHBoxLayout()
        bot_widget = QWidget()

        grid_button_widget = QWidget()
        grid_button_layout = QVBoxLayout()
        grid_button_layout.addWidget(self.button_grid)
        grid_button_layout.addWidget(self.button_draw)
        grid_button_layout.addWidget(self.button_remove)
        grid_button_layout.addWidget(self.button_disable_modes)
        grid_button_widget.setLayout(grid_button_layout)

        horizontal_layout_top.addWidget(grid_button_widget)
        horizontal_layout_top.addWidget(self.point_clicker_view)
        top_widget.setLayout(horizontal_layout_top)

        horizontal_layout_bot.addWidget(self.video_player)
        horizontal_layout_bot.addWidget(self.save_button)
        bot_widget.setLayout(horizontal_layout_bot)

        vertical_layout.addWidget(top_widget)
        vertical_layout.addWidget(bot_widget)
        self.setLayout(vertical_layout)

        self.button_draw.clicked.connect(self.set_draw_mode)
        self.button_remove.clicked.connect(self.set_remove_mode)
        self.button_disable_modes.clicked.connect(self.disable_modes)
        self.save_button.clicked.connect(self.save)
        self.point_clicker_view.point_added.connect(self.video_player.increment_frame)
        self.button_grid.buttonSignal.connect(self.point_clicker_view.set_laser_index)

    def save(self) -> None:
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Are you sure?")
        dlg.setText(
            f"You chose {self.cycle_start_index} and {self.cycle_end_index} as start and end frame. Is this ok?"
        )
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setIcon(QMessageBox.Question)
        button = dlg.exec()

        if button == QMessageBox.No:
            return

        # TODO: Implement me

    def set_draw_mode(self) -> None:
        self.point_clicker_view.DRAW_MODE_on()
        self.point_clicker_view.REMOVE_MODE_off()

    def set_remove_mode(self) -> None:
        self.point_clicker_view.REMOVE_MODE_on()
        self.point_clicker_view.DRAW_MODE_off()

    def disable_modes(self) -> None:
        self.point_clicker_view.REMOVE_MODE_off()
        self.point_clicker_view.DRAW_MODE_off()
