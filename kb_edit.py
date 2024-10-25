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
        # If you set a border, the border is part of the label!
        self.image_label.setStyleSheet("background-color: black;")

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.select_button)
        btn_layout.addWidget(self.default_button)
        btn_layout.addWidget(self.reset_button)

        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)
        self.setWindowTitle("Ken Burns Effect tools")
        self.setGeometry(300, 300, 500, 400)
        self.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Q:
            self.close()
        if event.key() == Qt.Key_R:
            self.handle_reset_parameters()
        if event.key() == Qt.Key_Escape:
            print("Esc pressed")

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

        pos = self.mapPosToPixmap(event)
        if pos is None:
            return

        self.drawing = True
        box = self.boxes[self.current_box]

        box.begin = pos
        box.end = box.begin

    def mouseMoveEvent(self, event):
        if not self.drawing:
            return

        pos = self.mapPosToPixmap(event)
        if pos is None:
            return

        box = self.boxes[self.current_box]

        (box.begin, box.end) = self.enforce_16_9_ratio(box.begin, pos)

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

        print(
            f"Current box: {self.current_box}, "
            f"Rectangle drawn: ({rect.topLeft().x()}, {rect.topLeft().y()}), "
            f"                 ({rect.bottomRight().x()}, {rect.bottomRight().y()})\n"
            f"X, Y, W, H ({rect.topLeft().x()}, {rect.topLeft().y()}, {rect.width()}, {rect.height()})\n"
        )

        if self.current_box == "end":
            rect_start = self.mapRectToImage(
                QRect(self.boxes["start"].begin, self.boxes["start"].end)
            ).normalized()
            rect_end = self.mapRectToImage(
                QRect(self.boxes["end"].begin, self.boxes["end"].end)
            ).normalized()

            x1 = rect_start.x()
            x2 = rect_end.x()
            y1 = rect_start.y()
            y2 = rect_end.y()
            w1 = rect_start.width()
            w2 = rect_end.width()

            print(
                f"ffmpeg -i picture.jpg -vf \"zoompan=z='1+(({w2}/{w1})-1)*(on/duration)':x='{x1}+({x2}-{x1})*(on/duration)':y='{y1}+({y2}-{y1})*(on/duration)':d=300:s=1920x1080\" -t 10 output.mp4"
            )
        else:
            self.current_box = "end"

    def mapRectToImage(self, rect):
        return QRect(
            int(rect.x() * self.image_scale_factor),
            int(rect.y() * self.image_scale_factor),
            int(rect.width() * self.image_scale_factor),
            int(rect.height() * self.image_scale_factor),
        )

    def mapPosToPixmap(self, event):
        if not self.image_label.geometry().contains(event.pos()):
            return None

        label_pos = event.pos() - self.image_label.pos()
        # print(f"Label position: {label_pos}, Event position: {event.pos()}")

        pixmap_size = self.original_scaled_pixmap.size()
        label_size = self.image_label.size()

        offset_x = (label_size.width() - pixmap_size.width()) / 2
        offset_y = (label_size.height() - pixmap_size.height()) / 2

        x = label_pos.x() - offset_x
        y = label_pos.y() - offset_y

        # Not sure why we need this "-1 pixel" but it looks good
        x = min(max(0, x), pixmap_size.width() - 1)
        y = min(max(0, y), pixmap_size.height())

        return QPoint(int(x), int(y))

    def enforce_16_9_ratio(self, top_left, bottom_right):
        # Calculate the current width and height of the rectangle
        current_width = abs(bottom_right.x() - top_left.x())
        current_height = abs(bottom_right.y() - top_left.y())

        # Calculate the desired height for a 16:9 ratio, given the current width
        desired_height = current_width * 9 / 16

        # Calculate the desired width for a 16:9 ratio, given the current height
        desired_width = current_height * 16 / 9

        # Create copies of the original QPoint objects to avoid mutating the input
        new_bottom_right = QPoint(bottom_right)

        # Determine whether to adjust width or height
        if current_height > desired_height:
            # Adjust the height to maintain 16:9 ratio
            if new_bottom_right.y() > top_left.y():
                new_bottom_right.setY(int(top_left.y() + desired_height))
            else:
                new_bottom_right.setY(int(top_left.y() - desired_height))
        else:
            # Adjust the width to maintain 16:9 ratio
            if new_bottom_right.x() > top_left.x():
                new_bottom_right.setX(int(top_left.x() + desired_width))
            else:
                new_bottom_right.setX(int(top_left.x() - desired_width))

        return top_left, new_bottom_right

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
