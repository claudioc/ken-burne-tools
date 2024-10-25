#!/usr/bin/env python3
import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QFont, QColor
from PyQt5.QtCore import Qt, QRect, QTimer, QPoint
from dataclasses import dataclass


@dataclass
class Box:
    begin: tuple = None
    end: tuple = None


pen_color = {
    "start": Qt.green,
    "end": Qt.red,
}


class ImageViewerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.boxes = {
            "start": Box(),
            "end": Box(),
        }
        self.current_box = "start"
        self.original_scaled_pixmap = None
        self.original_pixmap_size = None
        self.drawing = False
        self.mode = "edit"

        # Animation parameters
        # self.duration = 5000  # Animation duration in ms
        # self.fps = 30  # Frames per second
        # self.total_frames = int(self.duration / (1000 / self.fps))
        # self.current_frame = 0
        # self.timer = QTimer()
        # self.timer.timeout.connect(self.update_frame)

    # def update_frame(self):
    #     if self.current_frame >= self.total_frames:
    #         self.timer.stop()
    #         return

    #     rect_start = QRect(self.boxes["start"].begin, self.boxes["start"].end)
    #     rect_end = QRect(self.boxes["end"].begin, self.boxes["end"].end)

    #     # Interpolate the rectangle position
    #     t = self.current_frame / self.total_frames
    #     interpolated_rect = self.interpolate_rect(rect_start, rect_end, t)

    #     # Crop the original image and resize it to fit the QLabel
    #     cropped_pixmap = self.original_scaled_pixmap.copy(interpolated_rect)
    #     scaled_pixmap = cropped_pixmap.scaled(
    #         self.image_label.size(), aspectRatioMode=True
    #     )

    #     # Update the QLabel with the new frame
    #     self.image_label.setPixmap(scaled_pixmap)

    #     self.current_frame += 1

    # def interpolate_rect(self, start_rect, end_rect, t):
    #     """Interpolate between start and end rectangles based on t (0 to 1)."""
    #     x = start_rect.x() + t * (end_rect.x() - start_rect.x())
    #     y = start_rect.y() + t * (end_rect.y() - start_rect.y())
    #     width = start_rect.width() + t * (end_rect.width() - start_rect.width())
    #     height = start_rect.height() + t * (end_rect.height() - start_rect.height())
    #     return QRect(int(x), int(y), int(width), int(height))

    def __setattr__(self, key, value):
        if key == "current_box" and value not in self.boxes.keys():
            raise ValueError(f"Invalid value for current_box: {value}")
        super().__setattr__(key, value)

    def initUI(self):
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setText("No image selected")
        self.select_button = QPushButton("Select Image", self)
        self.select_button.clicked.connect(self.handle_open_image)
        self.default_button = QPushButton("Open default image", self)
        self.default_button.clicked.connect(self.handle_open_default_image)
        self.reset_button = QPushButton("Reset", self)
        self.reset_button.clicked.connect(self.handle_reset_parameters)
        self.image_scale_factor = 1

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.image_label, alignment=Qt.AlignHCenter)
        w = int(1920 / 2)
        h = int(w * 9 / 16)
        self.image_label.setFixedSize(w, h)
        self.image_label.setStyleSheet("border: 2px solid silver")

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.select_button)
        btn_layout.addWidget(self.default_button)
        btn_layout.addWidget(self.reset_button)

        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)
        self.setWindowTitle("PyQt5 Image Viewer with Rectangle Drawing")
        self.setGeometry(300, 300, 500, 400)
        self.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Q:
            self.close()
        if event.key() == Qt.Key_R:
            self.handle_reset_parameters()
        # if event.key() == Qt.Key_P:
        #     self.handle_preview()
        if event.key() == Qt.Key_Escape:
            print("Esc pressed")

    # def resizeEvent(self, event):
    #     """Override the resize event to enforce a 16:9 aspect ratio (1080p ratio)."""
    #     new_width = self.width()
    #     new_height = int(new_width * 9 / 16)  # Enforce the 16:9 ratio

    #     # If the calculated height is too large for the current window height, adjust the width
    #     if new_height > self.height():
    #         new_height = self.height()
    #         new_width = int(new_height * 16 / 9)

    #     # Resize the QLabel to maintain the aspect ratio
    #     self.image_label.setFixedSize(new_width, new_height)

    #     super().resizeEvent(event)  # Call the base class resize event

    # def handle_preview(self):
    #     if self.boxes["start"].begin is None or self.boxes["end"].begin is None:
    #         return

    #     if self.timer.isActive() or self.mode == "preview":
    #         self.timer.stop()
    #         self.update_image()
    #         self.mode = "edit"
    #     else:
    #         self.mode = "preview"
    #         self.current_frame = 0
    #         self.timer.start(int(1000 / self.fps))

    def handle_open_image(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Image Files (*.png *.jpg)"
        )

        if file_name:
            self.render_image(file_name)

    def handle_open_default_image(self):
        self.render_image("/Users/claudioc/Projects/pykb/picture.jpg")

    def handle_reset_parameters(self):
        self.current_box = "start"
        self.boxes["start"] = Box()
        self.boxes["end"] = Box()
        self.drawing = False
        if self.original_scaled_pixmap:
            self.image_label.setPixmap(self.original_scaled_pixmap)

    def render_image(self, file_name):
        pixmap = QPixmap(file_name)
        if pixmap is None:
            return

        self.current_box = "start"
        box = self.boxes[self.current_box]
        box.begin = None
        box.end = None
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.original_scaled_pixmap = scaled_pixmap
        self.original_pixmap_size = pixmap.size()
        self.image_label.setPixmap(scaled_pixmap)
        self.image_scale_factor = pixmap.width() / scaled_pixmap.width()

        self.image_label.setText("")

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        pos = self.scaleMousePos(event)
        if pos is None:
            return

        self.drawing = True
        box = self.boxes[self.current_box]

        box.begin = pos
        box.end = box.begin

    def mouseMoveEvent(self, event):
        if not self.drawing:
            return

        pos = self.scaleMousePos(event)
        if pos is None:
            return

        box = self.boxes[self.current_box]

        box.end = pos

        self.update_image()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        if not self.drawing:
            return

        self.drawing = False

        box = self.boxes[self.current_box]

        self.update_image()

        rect = QRect(box.begin, box.end).normalized()

        remapped_rect = QRect(
            rect.x() * self.image_scale_factor,
            rect.y() * self.image_scale_factor,
            rect.width() * self.image_scale_factor,
            rect.height() * self.image_scale_factor,
        )

        print(
            f"Current box: {self.current_box}, "
            f"Rectangle drawn: Top-left ({rect.topLeft().x()}, {rect.topLeft().y()}), "
            f"Bottom-right ({rect.bottomRight().x()}, {rect.bottomRight().y()})\n"
        )

        print(
            "Remapped"
            f"Rectangle drawn: Top-left ({remapped_rect.topLeft().x()}, {remapped_rect.topLeft().y()}), "
            f"Bottom-right ({remapped_rect.bottomRight().x()}, {remapped_rect.bottomRight().y()})\n\n"
        )

        if self.current_box == "start":
            self.current_box = "end"

    def scaleMousePos(self, event):
        label_pos = event.pos() - self.image_label.pos()
        # print(f"Label position: {label_pos}, Event position: {event.pos()}")

        pixmap_size = self.original_pixmap_size
        label_size = self.image_label.size()

        offset_x = (label_size.width() - pixmap_size.width()) / 2
        offset_y = (label_size.height() - pixmap_size.height()) / 2

        x = label_pos.x() - offset_x
        y = label_pos.y() - offset_y

        if 0 <= x <= pixmap_size.width() and 0 <= y <= pixmap_size.height():
            return QPoint(int(x), int(y))
        else:
            return None

    def update_image(self):
        if not self.original_scaled_pixmap:
            return

        pixmap = self.original_scaled_pixmap.copy()
        painter = QPainter(pixmap)
        self.draw_box(painter, self.current_box, not self.drawing)

        if self.current_box == "end":
            self.draw_box(painter, "start", True)

        painter.end()
        self.image_label.setPixmap(pixmap)

    def draw_box(self, painter, box_name, solid=False):
        box = self.boxes[box_name]
        # Normalized, always put the label in the right place
        rect = QRect(box.begin, box.end).normalized()
        painter.setPen(self.pen_for(box_name, solid=solid))
        painter.drawRect(rect)
        painter.setFont(QFont("Arial", 12))
        painter.drawText(rect.left(), rect.bottom() + 20, box_name.capitalize())

    def pen_for(self, box_name, solid=False):
        return QPen(
            pen_color[box_name],
            2,
            Qt.SolidLine if solid else Qt.DashLine,
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageViewerApp()
    sys.exit(app.exec_())
