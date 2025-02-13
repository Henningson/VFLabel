from typing import List

import numpy as np
import PyQt5.Qt
import PyQt5.QtCore
from PyQt5.QtCore import QPointF, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QCursor, QImage, QPen
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsView, QMenu, QMessageBox

import VFLabel.gui_widgets.ellipseWithID as ellipseWithID
import VFLabel.gui_graphics_view.zoomableVideo as zoomableVideo
import VFLabel.utils.enums as enums


class ManualPointClicker(zoomableVideo.ZoomableVideo):
    point_added = pyqtSignal()
    point_removed = pyqtSignal(int, int)
    signal_increment_frame = pyqtSignal(bool)
    signal_decrement_frame = pyqtSignal(bool)

    def __init__(
        self,
        video: List[QImage],
        grid_width: int = 18,
        grid_height: int = 18,
        parent=None,
    ):
        super(ManualPointClicker, self).__init__(video, parent)
        self._draw_mode = enums.DRAW_MODE.OFF
        self._remove_mode = enums.DRAW_MODE.OFF

        self._pointpen = QPen(QColor(128, 255, 128, 255))
        self._pointbrush = QBrush(QColor(128, 255, 128, 128))

        self._pointsize: int = 7

        self._point_items: List[QGraphicsEllipseItem] = []

        self._num_frames = len(video)

        self._image_width = video[0].width()
        self._image_height = video[0].height()

        # Point positions is 4D Numpy array of size
        # CYCLE_LENGTH x GRID_HEIGHT x GRID_WIDTH x 2
        # For each frame, we can have at max grid_height*grid_width indices with 2 positions each.
        # That should make it really easy to assign points to their specific laser index.
        # Everything is indexed as nan at first. Makes it easy to find already set points.
        self.point_positions = (
            np.zeros([len(video), grid_height, grid_width, 2]) * np.nan
        )
        self.y_index: int = None
        self.x_index: int = None

        self._draw_mode = enums.DRAW_MODE.OFF
        self._remove_mode = enums.REMOVE_MODE.OFF

    def keyPressEvent(self, event) -> None:
        if event.key() == PyQt5.QtCore.Qt.Key_E:
            self.toggle_draw_mode()

        if event.key() == PyQt5.QtCore.Qt.Key_E:
            self.toggle_remove_mode()

        if event.key() == PyQt5.QtCore.Qt.Key_Right:
            self.frame_forward()
        elif event.key() == PyQt5.QtCore.Qt.Key_Left:
            self.frame_backward()

    def mousePressEvent(self, event) -> None:
        if (
            self._draw_mode == enums.DRAW_MODE.OFF
            and self._remove_mode == enums.REMOVE_MODE.OFF
        ):
            super().mousePressEvent(event)

        global_pos = event.pos()
        pos = self.mapToScene(global_pos)

        if self._draw_mode == enums.DRAW_MODE.ON:
            self.add_point(pos)
            self.setCursor(QCursor(PyQt5.QtCore.Qt.CrossCursor))
            return

        if self._remove_mode == enums.REMOVE_MODE.ON:
            self.remove_point(pos)
            self.setCursor(QCursor(PyQt5.QtCore.Qt.CrossCursor))
            return

    def contextMenuEvent(self, event) -> None:
        """
        Opens a context menu with options for zooming in and out.

        :param event: The QContextMenuEvent containing information about the context menu event.
        :type event: QContextMenuEvent
        """
        menu = QMenu()
        menu.addAction("Zoom in\tMouseWheel Up", self.zoomIn)
        menu.addAction("Zoom out\tMouseWheel Down", self.zoomOut)
        menu.addAction("Toggle Edit Mode\tE", self.toggle_draw_mode)
        menu.addAction("Draw Mode ON", self.DRAW_MODE_on)
        menu.addAction("Draw Mode OFF", self.DRAW_MODE_off)
        menu.addAction("Frame forward\tRight Arrow", self.frame_forward)
        menu.addAction("Frame backward\tLeft Arrow", self.frame_backward)
        menu.addAction("Reset View", self.zoomReset)
        menu.exec_(event.globalPos())

    def enterEvent(self, event):
        super().enterEvent(event)
        self.setCursor(QCursor(PyQt5.QtCore.Qt.CrossCursor))

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.setCursor(QCursor(PyQt5.QtCore.Qt.CrossCursor))

    def frame_forward(self):
        if self._current_frame == self._num_frames - 1:
            return
        self.change_frame(self._current_frame + 1)
        self.signal_increment_frame.emit(True)

    def frame_backward(self):
        if self._current_frame >= self._num_frames:
            return
        self.change_frame(self._current_frame - 1)
        self.signal_decrement_frame.emit(True)

    def toggle_remove_mode(self) -> None:
        self._draw_mode = enums.DRAW_MODE.OFF

        if self._remove_mode == enums.REMOVE_MODE.OFF:
            self._remove_mode = enums.REMOVE_MODE.ON
        elif self._remove_mode == enums.REMOVE_MODE.ON:
            self._remove_mode = enums.REMOVE_MODE.OFF
        else:
            raise ValueError()

    def toggle_draw_mode(self) -> None:
        self._remove_mode = enums.REMOVE_MODE.OFF

        if self._draw_mode == enums.DRAW_MODE.OFF:
            self._draw_mode = enums.DRAW_MODE.ON
        elif self._draw_mode == enums.DRAW_MODE.ON:
            self._draw_mode = enums.DRAW_MODE.OFF
        else:
            raise ValueError()

    def DRAW_MODE_on(self) -> None:
        self.setDragMode(QGraphicsView.NoDrag)
        self.setCursor(QCursor(PyQt5.QtCore.Qt.CrossCursor))
        self._draw_mode = enums.DRAW_MODE.ON

    def DRAW_MODE_off(self) -> None:
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setCursor(QCursor(PyQt5.QtCore.Qt.ArrowCursor))
        self._draw_mode = enums.DRAW_MODE.OFF

    def REMOVE_MODE_on(self) -> None:
        self.setDragMode(QGraphicsView.NoDrag)
        self.setCursor(QCursor(PyQt5.QtCore.Qt.CrossCursor))
        self._remove_mode = enums.REMOVE_MODE.ON

    def REMOVE_MODE_off(self) -> None:
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setCursor(QCursor(PyQt5.QtCore.Qt.ArrowCursor))
        self._remove_mode = enums.REMOVE_MODE.OFF

    def get_draw_mode(self) -> enums.DRAW_MODE:
        return self._draw_mode

    def get_remove_mode(self) -> enums.REMOVE_MODE:
        return self._remove_mode

    def remove_point(self, point: QPointF) -> None:
        clicked_item = self.scene().itemAt(point, self.transform())

        if clicked_item in self._point_items:
            self.scene().removeItem(clicked_item)
            self._point_items.remove(clicked_item)
            x_id, y_id = clicked_item.getID()
            self.point_positions[:, y_id, x_id] = np.nan

            self.point_removed.emit(x_id, y_id)

    def add_point(self, point: QPointF) -> None:
        if self.y_index is None or self.x_index is None:
            msgWarning = QMessageBox()
            msgWarning.setText(
                "Please select a laser beam that corresponds to the laser point you want to label from the grid."
            )
            msgWarning.setIcon(QMessageBox.Warning)
            msgWarning.setWindowTitle("Caution")
            msgWarning.exec()
            return

        if point.x() < 0 or point.x() >= self._image_width:
            return

        if point.y() < 0 or point.y() >= self._image_height:
            return

        self.point_positions[self._current_frame, self.y_index, self.x_index] = [
            point.x(),
            point.y(),
        ]

        for ellipse_item in self._point_items:
            if ellipse_item.x_id == self.x_index and ellipse_item.y_id == self.y_index:
                return

        # Transformed point, such that ellipse center is at mouse position
        ellipse_item = ellipseWithID.GraphicEllipseItemWithID(
            point.x() - self._pointsize / 2,
            point.y() - self._pointsize / 2,
            self._pointsize,
            self._pointsize,
            self._pointpen,
            self._pointbrush,
            self.x_index,
            self.y_index,
        )
        self.scene().addItem(ellipse_item)
        self._point_items.append(ellipse_item)
        self.point_added.emit()

    def set_laser_index(self, x: int, y: int) -> None:
        self.y_index = y
        self.x_index = x

    def redraw(self) -> None:
        if self.images:
            self.set_image(self.images[self._current_frame])

        for point_item in self._point_items:
            self.scene().removeItem(point_item)
        self._point_items = []

        current_points = self.point_positions[self._current_frame].reshape(-1, 2)
        filtered_points = current_points[~np.isnan(current_points).any(axis=1)]
        ids = self.get_point_indices()[:, [2, 1]]
        for point, point_id in zip(filtered_points, ids):
            ellipse_item = ellipseWithID.GraphicEllipseItemWithID(
                point[0] - self._pointsize / 2,
                point[1] - self._pointsize / 2,
                self._pointsize,
                self._pointsize,
                self._pointpen,
                self._pointbrush,
                point_id[0],
                point_id[1],
            )
            self.scene().addItem(ellipse_item)
            self._point_items.append(ellipse_item)

    def get_point_indices(self) -> np.array:
        mask = ~np.isnan(self.point_positions).any(axis=-1)

        # Get x, y indices of valid points
        return np.argwhere(mask)
