from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import QObject, Qt, QSettings
from model import ImageViewerModel
from view import ImageViewerView
import numpy as np
import os

class ImageViewerController(QObject):
    def __init__(self):
        super().__init__()
        self.model = ImageViewerModel()

        self.settings = QSettings("jameslee0227@gmail.com", "ImageViewer")
        self.recent_folders = self.load_recent_folders()

        self.view = ImageViewerView(self)
        self.labels_visible = True
        self.overlay_data = {}

        # 모델 시그널을 뷰 슬롯에 연결
        self.model.image_changed.connect(self.view.display_image)
        self.model.labels_changed.connect(self.view.display_labels)

        # 뷰 시그널을 컨트롤러 슬롯에 연결
        self.view.tree_view.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def load_recent_folders(self):
        #folders = self.settings.value("recent_folders", [])
        #return list(dict.fromkeys(folders))[:10]
        return self.settings.value("recent_folders", [])
    def save_recent_folders(self):
        self.settings.setValue("recent_folders", self.recent_folders)
    def add_to_recent_folder(self, folder_path):
        if folder_path in self.recent_folders:
            self.recent_folders.remove(folder_path)
        self.recent_folders.insert(0, folder_path)
        self.recent_folders = self.recent_folders[:10] # 최대 10개 유지
        self.save_recent_folders()
        self.view.update_recent_folders_menu()

    def on_selection_changed(self, selected, deselected):
        """트리 뷰에서 선택이 변경될 때 호출되는 메서드"""
        indexes = self.view.tree_view.selectionModel().selectedIndexes()
        if indexes:
            image_path = self.model.get_image_path(indexes[0])
            if image_path:
                self.load_image(image_path)

    def open_folder(self):
        """폴더 열기 대화상자를 표시하고 선택된 폴더를 설정"""
        last_folder = self.settings.value("last_folder","")
        folder_path = QFileDialog.getExistingDirectory(None, "Select Folder", last_folder)
        if folder_path:
            self.model.set_folder(folder_path)
            self.view.update_tree_view(folder_path)
            self.settings.setValue("last_folder", folder_path)
            self.add_to_recent_folder(folder_path)
    def open_recent_folder(self, folder_path):
        if folder_path and os.path.exists(folder_path):
            self.recent_folders.remove(folder_path)
            self.model.set_folder(folder_path)
            self.view.update_tree_view(folder_path)
            self.settings.setValue("last_folder", folder_path)
        self.recent_folders.insert(0, folder_path)
        self.recent_folders = self.recent_folders[:10]
        self.save_recent_folders()
        self.view.update_recent_folders_menu()


    def load_image(self, image_path):
        """이미지 로드 및 표시"""
        if image_path:
            self.view.save_scroll_position()
            self.model.image_changed.emit(image_path)
            if self.labels_visible:
                self.model.get_label_path(image_path)

    def create_cut_folder(self):
        """잘라내기 폴더 생성"""
        if not self.model.cut_folder_exists():
            self.model.create_cut_folder()

    def move_data_file(self):
        """현재 선택된 이미지 파일 이동"""
        self.create_cut_folder()
        selected_image = self.view.get_current_image_path()
        if selected_image:
            self.view.save_scroll_position()
            self.model.move_data_file(selected_image)

    def toggle_labels(self):
        """레이블 표시/숨김 전환"""
        self.labels_visible = not self.labels_visible
        self.view.toggle_labels()

    def get_rotated_bbox(self, class_id, x_center, y_center, width, height, angle):
        """주어진 라벨의 바운딩 박스를 회전 후 AABB로 변환"""
        cx, cy = x_center, y_center
        w, h = width / 2, height / 2

        # 바운딩 박스의 네 모서리 좌표
        corners = [
            (cx - w, cy - h),
            (cx + w, cy - h),
            (cx + w, cy + h),
            (cx - w, cy + h)
        ]

        # 모서리 좌표를 주어진 각도만큼 회전
        rotated_corners = [self.rotate_point(cx, cy, angle, px, py) for px, py in corners]

        # 회전된 좌표를 기준으로 AABB 계산
        x_coords, y_coords = zip(*rotated_corners)
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)

        new_w = x_max - x_min
        new_h = y_max - y_min
        new_cx = (x_min + x_max) / 2
        new_cy = (y_min + y_max) / 2

        return class_id, new_cx, new_cy, new_w, new_h

    def rotate_point(self, cx, cy, angle, px, py):
        """주어진 점(px, py)을 주어진 각도(angle)만큼 회전"""
        s = np.sin(np.radians(angle))
        c = np.cos(np.radians(angle))

        # 원점 기준 회전
        px -= cx
        py -= cy

        xnew = px * c - py * s
        ynew = px * s + py * c

        # 다시 원래 위치로 이동
        px = xnew + cx
        py = ynew + cy

        return px, py

    def save_overlay_data(self, item, class_id, center_x, center_y, width, height, angle):
        self.overlay_data[item] = {
            "class_id": class_id,
            "center_x": center_x,
            "center_y": center_y,
            "width": width,
            "height": height,
            "angle": angle
        }

    def get_overlay_data(self, item):
        return self.overlay_data.get(item, None)
