from PyQt5.QtWidgets import QMainWindow, QAction, QToolBar, QFileDialog
from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from tqdm import tqdm

import os
import json
import cv2
import VFLabel.gui
import VFLabel.cv
import VFLabel.gui.newProjectWidget, VFLabel.gui.mainMenuView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # general setup
        self.showMaximized()
        # self.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: rgb(255, 255, 255);
            }

            QMenuBar {
                background: rgb(240, 248, 255);       /* background*/
                color: rgb(0, 0, 0);        /* text color*/
                border-top: 1px solid rgb(211, 211, 211);
                /*border-bottom: 1px solid rgb(211, 211, 211);*/
            }
            QToolBar {
                background: rgb(240, 248, 255);       /* background*/
                color: rgb(0, 0, 0);       /* text color*/
                /*border-top: 1px solid rgb(211, 211, 211);*/
                border-bottom: 1px solid rgb(211, 211, 211);
            }
            """
        )

        # setup menu bar
        self.setStatusBar(self.statusBar())
        self.menubar = self.menuBar()

        # file submenu
        file_menu = self.menubar.addMenu("&File")
        file_menu.addAction("Save", self.save_current_state)
        file_menu.addAction(
            "Load Glottis Segmentation from Folder",
            self.load_glottis_segmentation_folder,
        )

        file_menu.addAction(
            "Load glottis segmentation from Video", self.load_glottis_segmentation_video
        )

        # menu close button
        menu_close_window = QAction("Close current window", self)
        menu_close_window.triggered.connect(self.close_current_window)
        self.menubar.addAction(menu_close_window)

        # icons for toolbar - icons from license-free page: https://uxwing.com/
        close_icon_path = "assets/icons/close-square-line-icon.svg"
        save_icon_path = "assets/icons/check-mark-box-line-icon.svg"

        # setup tool bar
        self.toolbar = QToolBar()

        # tool close button
        tool_close_window = QAction(
            QIcon(close_icon_path), "Close current window", self
        )
        tool_close_window.setToolTip("Close current window  Ctrl+c")
        tool_close_window.setShortcut("Ctrl+c")
        tool_close_window.triggered.connect(self.close_current_window)
        self.toolbar.addAction(tool_close_window)

        # tool save button
        self.tool_save_window = QAction(
            QIcon(f"{save_icon_path}"), "Save current State", self
        )
        self.tool_save_window.setToolTip("Save current state  Ctrl+s")
        self.tool_save_window.setShortcut("Ctrl+s")
        self.tool_save_window.triggered.connect(self.save_current_state)
        self.toolbar.addAction(self.tool_save_window)

        self.addToolBar(self.toolbar)

        self.open_start_window()

        self.show()

    def open_start_window(self):
        self.menubar.setVisible(False)
        self.toolbar.setVisible(False)
        # new title
        self.setWindowTitle("HASEL - Start Menu")

        # setup window and its signals
        self.start_window = VFLabel.gui.startWindowView.StartWindowView(self)
        self.start_window.signal_open_main_menu.connect(self.open_main_menu)

        # make it visible in main window
        self.setCentralWidget(self.start_window)

    def open_main_menu(self, project_path):
        self.menubar.setVisible(True)
        self.toolbar.setVisible(True)
        self.tool_save_window.setVisible(False)

        # new title
        self.setWindowTitle(f"HASEL - Main Menu - {project_path}")

        # setup window and its signals
        self.main_menu = VFLabel.gui.mainMenuView.MainMenuView(project_path, self)
        self.main_menu.signal_open_vf_segm_window.connect(
            self.open_vf_segmentation_window
        )
        self.main_menu.signal_open_pt_label_window.connect(
            self.open_point_labeling_window
        )
        self.main_menu.signal_open_glottis_segm_window.connect(
            self.open_glottis_segmentation_window
        )
        self.main_menu.signal_close_main_menu_window.connect(self.open_start_window)

        # make it visible in main window
        self.setCentralWidget(self.main_menu)

    def open_vf_segmentation_window(self, project_path):
        self.tool_save_window.setVisible(True)
        # new title
        self.setWindowTitle(f"HASEL - VF segmentation - {project_path}")

        # setup window and its signals
        self.vf_segm_window = (
            VFLabel.gui.vocalfoldSegmentationView.VocalfoldSegmentationView(
                project_path, self
            )
        )
        self.vf_segm_window.signal_open_main_menu.connect(self.open_main_menu)

        # make it visible in main window
        self.setCentralWidget(self.vf_segm_window)

    def open_glottis_segmentation_window(self, project_path):
        self.tool_save_window.setVisible(True)
        # new title
        self.setWindowTitle(f"HASEL - Glottis segmentation - {project_path}")

        # setup window and its signals
        self.glottis_segm_window = (
            VFLabel.gui.glottisSegmentationView.GlottisSegmentationView(
                project_path, self
            )
        )
        self.glottis_segm_window.signal_open_main_menu.connect(self.open_main_menu)

        # make it visible in main window
        self.setCentralWidget(self.glottis_segm_window)

    def open_point_labeling_window(self, project_path):
        self.tool_save_window.setVisible(True)
        # new title
        self.setWindowTitle(f"HASEL - Point Labeling - {project_path}")

        # setup window and its signals
        self.pt_labeling_window = VFLabel.gui.pointLabelingView.PointLabelingView(
            project_path, self
        )
        self.pt_labeling_window.signal_open_main_menu.connect(self.open_main_menu)

        # make it visible in main window
        self.setCentralWidget(self.pt_labeling_window)

    def close_current_window(self) -> None:
        # called when "close current window" in menubar is triggered
        self.centralWidget().close_window()

    def save_current_state(self) -> None:
        self.centralWidget().save_current_state()

    def load_glottis_segmentation_folder(self) -> None:
        dir_path = QFileDialog.getExistingDirectory(
            caption="Folder containing the segmentation images"
        )

        segmentations = []
        for image_file in sorted(os.listdir(dir_path)):
            image_path = os.path.join(dir_path, image_file)
            segmentation = cv2.imread(image_path, 0)
            segmentations.append(segmentation)

    def load_glottis_segmentation_video(self) -> None:
        video_path, _ = QFileDialog.getOpenFileName(
            self,
            "Video of the glottis segmentation",
            "Only video-files(*.mp4 *.avi)",
        )

        video = VFLabel.io.data.read_video(video_path)
        self.generate_glottis_data(video)

    def generate_glottis_data(self, segmentations) -> None:
        midlines = [
            VFLabel.cv.analysis.glottal_midline(image) for image in tqdm(segmentations)
        ]

        self.save_segmentations_and_midlines(segmentations, midlines)
        self.update_glottis_progress()
        self.open_main_menu(self.centralWidget().project_path)

    def save_segmentations_and_midlines(self, segmentations, midlines) -> None:
        segmentation_path = os.path.join(
            self.centralWidget().project_path, "glottis_segmentation"
        )
        glottal_midlines_path = os.path.join(
            self.centralWidget().project_path, "glottal_midlines.json"
        )

        glottal_midline_dict = {}
        for frame_index, midline_points in enumerate(midlines):
            upper = midline_points[0]
            lower = midline_points[1]

            glottal_midline_dict[f"Frame{frame_index}"] = {
                "Upper": upper.tolist() if upper is not None else [-1, -1],
                "Lower": lower.tolist() if lower is not None else [-1, -1],
            }

        with open(glottal_midlines_path, "w+") as outfile:
            json.dump(glottal_midline_dict, outfile)

        for frame_index, seg in enumerate(segmentations):
            image_save_path = os.path.join(segmentation_path, f"{frame_index:05d}.png")
            cv2.imwrite(image_save_path, seg)

    def update_glottis_progress(self):
        progress_state_path = os.path.join(
            self.centralWidget().project_path, "progress_status.json"
        )

        with open(progress_state_path, "r+") as prgrss_file:
            file = json.load(prgrss_file)
            file["progress_gl_seg"] = "finished"
            prgrss_file.seek(0)
            prgrss_file.truncate()
            json.dump(file, prgrss_file, indent=4)
