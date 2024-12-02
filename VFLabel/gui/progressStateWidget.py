import sys

from PyQt5.QtWidgets import (
    QWidget,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QTextEdit,
    QLabel,
    QApplication,
)
from PyQt5.QtCore import Qt
import PyQt5.QtCore as QtCore


class ProgressStateWidget(QWidget):

    progress_signal = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.init_window()

    def init_window(self):
        # definition of question text
        question_text = QLabel(
            "Did you finish this step \n or would you like to continue next time?"
        )
        question_text.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        # create finish and toBeContinued btns
        btn_finished = QPushButton("Yes, I am finished", self)
        btn_finished.setToolTip("This <b>button</b> ...")
        btn_finished.setFixedSize(120, 40)
        btn_continue = QPushButton("Continue next time", self)
        btn_continue.setToolTip("This <b>button</b> ...")
        btn_continue.setFixedSize(120, 40)

        # add functionality to btns
        btn_continue.clicked.connect(self.process_to_be_continued)
        btn_finished.clicked.connect(self.process_finished)

        # define layout and insert all elements
        layout_v = QVBoxLayout()
        layout_h_btn = QHBoxLayout()
        layout_h_text = QHBoxLayout()

        layout_h_text.addStretch(1)
        layout_h_text.addWidget(question_text)
        layout_h_text.addStretch(1)

        layout_h_btn.addStretch(1)
        layout_h_btn.addWidget(btn_finished)
        layout_h_btn.addStretch(1)
        layout_h_btn.addWidget(btn_continue)
        layout_h_btn.addStretch(1)

        layout_v.addLayout(layout_h_text)
        layout_v.addStretch(1)
        layout_v.addLayout(layout_h_btn)
        layout_v.addStretch(1)

        self.setLayout(layout_v)

        # hide 'x' close button
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)

        # general setup
        self.setGeometry(300, 300, 100, 100)
        self.setWindowTitle("Update progress")
        self.show()

    def process_finished(self):
        # emit current progress
        self.progress_signal.emit("finished")
        self.deleteLater()

    def process_to_be_continued(self):
        # emit current progress
        self.progress_signal.emit("in progress")
        self.deleteLater()


# app = QApplication(sys.argv)
# w = ProgressStateWidget()
# sys.exit(app.exec_())