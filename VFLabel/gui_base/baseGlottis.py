import json
import os
import sys

import numpy as np
from PyQt5.QtCore import QEventLoop, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QVBoxLayout

import VFLabel.gui_base
import VFLabel.gui_base.baseWindow as baseWindow
import VFLabel.gui_view.viewGlottis
import VFLabel.gui_widgets.progressState
import VFLabel.gui_view.viewVocalfold
import VFLabel.io
import VFLabel.utils.utils


class BaseGlottis(baseWindow.BaseWindow):

    signal_open_main_menu = pyqtSignal(str)

    def __init__(self, project_path, parent=None):
        super().__init__(parent)
        self.project_path = project_path
        self.init_window()

    def init_window(self) -> None:
        layout = QVBoxLayout()

        valid_extensions = (".mp4", ".avi")

        # find video file
        matching_files = [
            os.path.join(self.project_path, f)
            for f in os.listdir(self.project_path)
            if f.endswith(valid_extensions)
        ]

        videodata = VFLabel.io.data.read_video(*matching_files)
        # Set up the zoomable view
        self.glottis_widget = VFLabel.gui_view.viewGlottis.GlottisSegmentationView(
            self.project_path, videodata
        )
        layout.addWidget(self.glottis_widget)

        self.setLayout(layout)
        # Show the window
        self.show()

    def save_current_state(self):
        self.glottis_widget.save()

    def update_progress(self, progress) -> None:
        self.progress = progress

    def update_save_state(self, state) -> None:
        if state:
            self.save_current_state()
        else:
            pass

    def help(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Help")
        dlg.setText(
            f"In this step of the pipeline, the glottis is segmented and the midline of the glottis is determined. We supply different neural network architectures."
        )
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.setIcon(QMessageBox.Information)
        dlg.exec()

    def close_window(self) -> None:

        # open window which asks if the data should be saved (again)
        self.save_state_window = VFLabel.gui_widgets.saveState.SaveStateWidget(self)

        # connect signal which updates save state
        self.save_state_window.save_state_signal.connect(self.update_save_state)

        # wait for save_state_window to close
        loop = QEventLoop()
        self.save_state_window.destroyed.connect(loop.quit)
        loop.exec_()

        # open window which asks for current state of this task
        self.progress_window = VFLabel.gui_widgets.progressState.ProgressStateWidget(
            self
        )

        # connect signal which updates progress state
        self.progress_window.progress_signal.connect(self.update_progress)

        # wait for progress_window to close
        loop = QEventLoop()
        self.progress_window.destroyed.connect(loop.quit)
        loop.exec_()

        # save new progress state
        self.progress_state_path = os.path.join(
            self.project_path, "progress_status.json"
        )

        with open(self.progress_state_path, "r+") as prgrss_file:
            file = json.load(prgrss_file)
            file["progress_gl_seg"] = self.progress
            prgrss_file.seek(0)
            prgrss_file.truncate()
            json.dump(file, prgrss_file, indent=4)

        # go back to main window
        self.signal_open_main_menu.emit(self.project_path)
