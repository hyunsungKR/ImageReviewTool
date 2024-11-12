import os.path
import os

import random
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                               QPushButton, QFileDialog, QLabel, QLineEdit,
                               QRadioButton, QButtonGroup)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap



class ImageWidget(QWidget):
    clicked = Signal(str)

    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        self.is_selected = False

        self.layout = QVBoxLayout(self)
        self.layout_sub = QHBoxLayout(self)

        self.image_label = QLabel()
        pixmap = QPixmap(image_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(pixmap)

        self.image_name = QLabel(os.path.basename(image_path))  # 이미지 파일 이름을 버튼 텍스트로 설정

        self.class_id_label = QLabel("Class ID:")
        self.class_id_input = QLineEdit()
        self.class_id_input.setFixedWidth(30)  # 너비 조정
        self.class_id_input.setText("3")  # 기본값을 2로 설정

        self.layout_sub.addWidget(self.image_label)
        self.layout_sub.addWidget(self.class_id_label)
        self.layout_sub.addWidget(self.class_id_input)
        self.layout.addLayout(self.layout_sub)
        self.layout.addWidget(self.image_name)  # 이미지 이름 버튼 추가


        self.setAutoFillBackground(True)
        self.update_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.image_path)

    def set_selected(self, selected):
        self.is_selected = selected
        self.update_style()

    def update_style(self):
        if self.is_selected:
            self.setStyleSheet("background-color: lightblue;")
        else:
            self.setStyleSheet("")

    def get_class_id(self):
        return self.class_id_input.text() or "3"  # 비어있으면 "2" 반환


class ImageListWindow(QWidget):
    images_selected = Signal(list)
    rotation_changed = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.Tool)
        self.setWindowTitle("Image List")
        self.setGeometry(100, 100, 400, 500)

        self.layout = QVBoxLayout(self)

        # 버튼 레이아웃
        self.button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Images")
        self.add_folder_button = QPushButton("Add Images from Folder")
        self.clear_button = QPushButton("Clear Images")
        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.add_folder_button)
        self.button_layout.addWidget(self.clear_button)
        self.layout.addLayout(self.button_layout)

        # 회전 옵션 레이아웃
        self.rotation_layout = QHBoxLayout()
        self.rotation_group = QButtonGroup(self)
        self.random_rotation_radio = QRadioButton("Random Rotation")
        self.fixed_rotation_radio = QRadioButton("Fixed Rotation")
        self.direction_light_radio = QRadioButton("Direction Light Rotation")
        self.rotation_input = QLineEdit()
        self.rotation_input.setPlaceholderText("Enter rotation angle")
        self.rotation_layout.addWidget(self.random_rotation_radio)
        self.rotation_layout.addWidget(self.fixed_rotation_radio)
        self.rotation_layout.addWidget(self.direction_light_radio)
        self.rotation_layout.addWidget(self.rotation_input)
        self.layout.addLayout(self.rotation_layout)

        self.rotation_group.addButton(self.random_rotation_radio)
        self.rotation_group.addButton(self.fixed_rotation_radio)
        self.rotation_group.addButton(self.direction_light_radio)
        self.random_rotation_radio.setChecked(True)
        self.rotation_input.setEnabled(False)

        # 스크롤 영역 설정
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)

        self.image_widgets = []
        self.last_directory = ""

        # 연결
        self.add_button.clicked.connect(self.add_images)
        self.add_folder_button.clicked.connect(self.add_images_from_folder)
        self.clear_button.clicked.connect(self.clear_images)
        self.random_rotation_radio.toggled.connect(self.update_rotation_input)
        self.fixed_rotation_radio.toggled.connect(self.update_rotation_input)
        self.direction_light_radio.toggled.connect(self.update_rotation_input)
        self.rotation_input.textChanged.connect(self.emit_rotation)

    def update_rotation_input(self):
        self.rotation_input.setEnabled(self.fixed_rotation_radio.isChecked())
        self.emit_rotation()

    def emit_rotation(self):
        if self.random_rotation_radio.isChecked():
            self.rotation_changed.emit(random.uniform(0, 360))
        elif self.fixed_rotation_radio.isChecked():
            try:
                angle = float(self.rotation_input.text())
                self.rotation_changed.emit(angle)
            except ValueError:
                pass
        elif self.direction_light_radio.isChecked():
            self.rotation_changed.emit(0) #DirectionLight는 각도를 직접 입력하지 않음.

    def get_image_data(self):
        return [(widget.image_path, widget.get_class_id()) for widget in self.image_widgets]

    def add_images(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Select Images", self.last_directory,
                                                     "Image Files (*.png *.jpg *.bmp)")
        if file_paths:
            self.last_directory = os.path.dirname(file_paths[0])
            self._add_images_to_list(file_paths)

    def add_images_from_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder", self.last_directory)
        if folder_path:
            self.last_directory = folder_path
            image_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path)
                           if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
            self._add_images_to_list(image_files)

    def _add_images_to_list(self, file_paths):
        for file_path in file_paths:
            image_widget = ImageWidget(file_path)
            image_widget.clicked.connect(self.on_image_clicked)
            self.scroll_layout.addWidget(image_widget)
            self.image_widgets.append(image_widget)

        if file_paths:
            self.images_selected.emit(file_paths)

    def clear_images(self):
        for widget in self.image_widgets:
            self.scroll_layout.removeWidget(widget)
            widget.deleteLater()
        self.image_widgets.clear()
        self.images_selected.emit([])

    def on_image_clicked(self, image_path):
        self.images_selected.emit([image_path])

    def update_selection(self, selected_paths):
        for widget in self.image_widgets:
            widget.set_selected(widget.image_path in selected_paths)

    def set_rotation_input(self, angle):
        self.rotation_input.setText(f"{angle:.2f}")
        self.emit_rotation()