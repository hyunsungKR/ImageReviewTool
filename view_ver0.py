import os
import random
from PySide6.QtWidgets import (QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
                               QGraphicsRectItem, QTreeView, QFileSystemModel, QSpinBox,
                               QToolBar, QWidget, QSplitter, QMenu, QVBoxLayout, QLabel, QPushButton,
                               QGraphicsPixmapItem, QHBoxLayout)
from PySide6.QtGui import QImage, QPixmap, QPen, QAction, QColor, QWheelEvent, QCursor, QGuiApplication, QShortcut, \
    QKeySequence, QPainter, QTransform
from PySide6.QtCore import Qt, QRectF, QFileInfo, QPoint, QPointF, QEvent

from image_list_window import ImageListWindow
import numpy as np
import cv2

class CustomGraphicsView(QGraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

    def wheelEvent(self, event: QWheelEvent):
        """휠 이벤트 처리 - 마우스 커서 중심으로 확대/축소"""
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            zoom_in_factor = 1.25
            zoom_out_factor = 1 / zoom_in_factor
            zoom_factor = zoom_in_factor if event.angleDelta().y() > 0 else zoom_out_factor

            # 현재 마우스 위치를 씬 좌표로 변환
            old_pos = self.mapToScene(event.position().toPoint())

            # 확대/축소 수행
            self.scale(zoom_factor, zoom_factor)

            # 확대/축소 후의 새로운 마우스 위치를 씬 좌표로 변환
            new_pos = self.mapToScene(event.position().toPoint())

            # 확대/축소 전후의 좌표 차이 계산
            delta = new_pos - old_pos

            # 이미지 위치 조정
            self.translate(delta.x(), delta.y())

            # 이미지가 뷰어보다 작아졌을 경우 중앙에 배치
            self.centerImageIfNecessary()
        else:
            super().wheelEvent(event)

    def centerImageIfNecessary(self):
        """이미지가 뷰어보다 작아졌을 경우 중앙에 배치"""
        scene_rect = self.sceneRect()
        view_rect = self.viewport().rect()
        view_rect = self.mapToScene(view_rect).boundingRect()

        # 수평 및 수직 이동 거리 계산
        dx = (view_rect.width() - scene_rect.width()) / 2 if view_rect.width() > scene_rect.width() else 0
        dy = (view_rect.height() - scene_rect.height()) / 2 if view_rect.height() > scene_rect.height() else 0

        # 씬의 사각형 영역을 조정하여 중앙에 배치
        self.setSceneRect(scene_rect.adjusted(-dx, -dy, dx, dy))

    def fitInView(self, rect, mode=Qt.KeepAspectRatio):
        """이미지를 뷰어에 맞추고 중앙에 배치"""
        super().fitInView(rect, mode)
        self.centerImageIfNecessary()


class ImageViewerZoomHandler:
    def __init__(self, graphics_view):
        self.graphics_view = graphics_view
        self.zoom_level = 1.0

    def zoom_in(self):
        """화면 확대"""
        self.zoom_level *= 1.2
        self.apply_zoom(1.2)

    def zoom_out(self):
        """화면 축소"""
        self.zoom_level /= 1.2
        self.apply_zoom(1/1.2)

    def apply_zoom(self, factor):
        """줌 레벨 적용"""
        old_center = self.graphics_view.mapToScene(self.graphics_view.viewport().rect().center())
        self.graphics_view.resetTransform()
        self.graphics_view.scale(self.zoom_level, self.zoom_level)
        self.graphics_view.centerOn(old_center)

        # 줌 레벨이 1.0 미만일 경우 중앙에 고정
        if self.zoom_level < 1.0:
            self.graphics_view.centerImageIfNecessary()


class ImageViewerPanHandler:  # 패닝 핸들러 클래스 정의
    def __init__(self, graphics_view):
        self.graphics_view = graphics_view
        self.is_panning = False
        self.last_pan_point = QPoint()

    def start_pan(self, pos):
        """패닝 시작"""
        self.is_panning = True
        self.last_pan_point = pos

    def pan(self, pos):
        """패닝 수행"""
        if self.is_panning:
            delta = self.last_pan_point - pos
            self.graphics_view.horizontalScrollBar().setValue(
                self.graphics_view.horizontalScrollBar().value() + delta.x())
            self.graphics_view.verticalScrollBar().setValue(
                self.graphics_view.verticalScrollBar().value() + delta.y())
            self.last_pan_point = pos

    def stop_pan(self):
        """패닝 종료"""
        self.is_panning = False


class ImageViewerView(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller  # 컨트롤러를 인스턴스 변수로 저장
        self.setGeometry(0, 0, 2560, 1440)  # 윈도우의 초기 위치와 크기 설정
        self.setWindowTitle("Image Viewer")  # 윈도우 제목 설정
        self.scroll_position = QPoint()  # 스크롤 위치 초기화

        # 중앙 위젯 설정
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # 스플리터 설정
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)

        # 왼쪽 레이아웃 설정 (큰 뷰어)
        self.graphics_view = CustomGraphicsView()
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        self.splitter.addWidget(self.graphics_view)

        # 오른쪽 레이아웃 설정
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout(self.right_widget)

        # zoom box 두 개 넣을 레이아웃
        self.zoom_box_layout = QHBoxLayout()
        self.right_layout.addLayout(self.zoom_box_layout)

        # 줌박스1 레이아웃 설정
        self.zoom_box1_layout = QVBoxLayout()
        self.zoom_spinbox1 = QSpinBox(self)
        self.zoom_spinbox1.setRange(1, 1000)
        self.zoom_spinbox1.setValue(250)
        self.zoom_box1_layout.addWidget(self.zoom_spinbox1)
        self.label_view1 = QLabel(self)
        self.label_view1.setFixedSize(400, 400)
        self.zoom_box1_layout.addWidget(self.label_view1)
        self.zoom_box_layout.addLayout(self.zoom_box1_layout)

        # 줌박스2 레이아웃 설정
        self.zoom_box2_layout = QVBoxLayout()
        self.zoom_spinbox2 = QSpinBox(self)
        self.zoom_spinbox2.setRange(1, 1000)
        self.zoom_spinbox2.setValue(500)
        self.zoom_box2_layout.addWidget(self.zoom_spinbox2)
        self.label_view2 = QLabel(self)
        self.label_view2.setFixedSize(400, 400)
        self.zoom_box2_layout.addWidget(self.label_view2)
        self.zoom_box_layout.addLayout(self.zoom_box2_layout)

        # 파일 시스템 모델 및 트리 뷰 설정 (탐색기)
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath("")
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.file_model)
        self.tree_view.setRootIsDecorated(False)
        self.tree_view.setSortingEnabled(True)
        self.tree_view.sortByColumn(0, Qt.AscendingOrder)
        self.tree_view.hideColumn(1)
        self.tree_view.hideColumn(2)
        self.tree_view.hideColumn(3)
        self.right_layout.addWidget(self.tree_view)

        self.splitter.addWidget(self.right_widget)
        self.splitter.setSizes([int(self.width() * 0.8), int(self.width() * 0.2)])

        # 파일 필터 설정
        self.file_model.setNameFilters(["*.png", "*.jpg", "*.jpeg"])
        self.file_model.setNameFilterDisables(False)

        # 트리 뷰 열고 닫는 버튼
        self.tree_open_close_button = QPushButton("Tree Open/Close")
        self.tree_open_close_button.clicked.connect(self.toggle_tree_open_close)
        self.right_layout.addWidget(self.tree_open_close_button)

        # 줌 및 패닝 핸들러 초기화
        self.zoom_handler = ImageViewerZoomHandler(self.graphics_view)
        self.pan_handler = ImageViewerPanHandler(self.graphics_view)

        # 메뉴 및 툴바 설정
        self.setup_menu()
        self.setup_toolbar()

        # 그래픽스 뷰 드래그 모드 설정
        self.graphics_view.setDragMode(QGraphicsView.ScrollHandDrag)

        # 트리 뷰 컨텍스트 메뉴 설정
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.open_context_menu)

        # Stemp image 이미지 리스트
        self.image_list_window = None
        self.show_image_list_button = QPushButton("Show Image List")
        self.show_image_list_button.clicked.connect(self.toggle_image_list_window)
        self.right_layout.addWidget(self.show_image_list_button)

        self.selected_overlay_images = []
        self.overlay_items = []
        self.current_overlay_index = 0

        # Stemp image Ctrl + S 이미지 저장
        self.save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.save_shortcut.activated.connect(self.save_overlay_image)

        # 회전
        self.current_rotation = 0

        # 미리보기
        self.preview_item = None
        self.graphics_view.viewport().installEventFilter(self)

        # 마우스 커서
        self.setMouseTracking(True)
        self.graphics_view.setMouseTracking(True)
        self.graphics_view.viewport().setMouseTracking(True)
        self.cursor_visible = True

        # 라벨 설정
        self.labels_visible = True
        self.label_items = []

        self.showMaximized()
        self.show()

    def toggle_tree_open_close(self):
        """트리뷰 열고 닫기 토글 메서드"""
        if self.tree_view.isExpanded(self.tree_view.rootIndex()):
            self.collapse_all(self.tree_view.rootIndex())
        else:
            self.expand_all(self.tree_view.rootIndex())

    def expand_all(self, index):
        """트리뷰의 모든 항목을 확장"""
        self.tree_view.expand(index)
        for i in range(self.file_model.rowCount(index)):
            child_index = self.file_model.index(i, 0, index)
            self.expand_all(child_index)

    def collapse_all(self, index):
        """트리뷰의 모든 항목을 축소"""
        self.tree_view.collapse(index)
        for i in range(self.file_model.rowCount(index)):
            child_index = self.file_model.index(i, 0, index)
            self.collapse_all(child_index)


    def toggle_image_list_window(self):
        """이미지 리스트 윈도우 토글 메서드"""
        if self.image_list_window is None:
            self.image_list_window = ImageListWindow(self)
            self.image_list_window.images_selected.connect(self.set_selected_overlay_images)
            self.image_list_window.rotation_changed.connect(self.set_rotation)

        if self.image_list_window.isVisible():
            self.image_list_window.hide()
        else:
            self.image_list_window.show()

    def set_selected_overlay_images(self, image_paths):
        """선택된 오버레이 이미지 설정 메서드"""
        self.selected_overlay_images = [QPixmap(path) for path in image_paths]
        self.current_overlay_index = 0 
        if self.image_list_window: 
            self.image_list_window.update_selection(image_paths)

    def save_overlay_image(self):
        """오버레이 이미지 저장 메서드"""
        if not hasattr(self, 'current_image_path') or not self.current_image_path:
            print("No image loaded")
            return

        # 현재 이미지의 경로와 파일명 가져오기
        current_dir = os.path.dirname(self.current_image_path)
        file_name = os.path.basename(self.current_image_path)
        file_name_without_ext, ext = os.path.splitext(file_name)

        # 상위 폴더 경로 가져오기
        parent_dir = os.path.dirname(current_dir)

        # 저장할 폴더 경로 생성
        save_dir = os.path.join(parent_dir, f"{os.path.basename(current_dir)}_Arg")

        # 상위 폴더가 없는 경우 현재 폴더에 저장
        if not os.path.exists(parent_dir):
            save_dir = os.path.join(current_dir, f"{file_name_without_ext}_Arg")

        # 저장할 폴더가 없으면 생성
        os.makedirs(save_dir, exist_ok=True)

        # 저장할 파일 경로 생성
        save_image_path = os.path.join(save_dir, f"{file_name_without_ext}{ext}")
        save_txt_path = os.path.join(save_dir, f"{file_name_without_ext}.txt")

        # 원본 이미지 로드
        original_image = QImage(self.current_image_path)  # 원본 이미지 로드

        # 원본 크기의 새 이미지 생성
        new_image = QImage(original_image.size(), QImage.Format_ARGB32)
        new_image.fill(Qt.transparent)

        # 새 이미지에 원본 이미지 그리기
        painter = QPainter(new_image)
        painter.drawImage(0, 0, original_image)

        # 오버레이 아이템 그리기
        for item in self.overlay_items:
            if isinstance(item, QGraphicsPixmapItem):
                pixmap = item.pixmap()
                pos = item.scenePos()
                if (pos.x() >= 0 and pos.y() >= 0 and
                        pos.x() + pixmap.width() <= original_image.width() and
                        pos.y() + pixmap.height() <= original_image.height()):
                    painter.drawPixmap(pos.toPoint(), pixmap)

        painter.end()

        new_image.save(save_image_path)
        print(f"Image saved: {save_image_path}")

        self.save_txt_file(save_txt_path)
        print(f"Text file saved: {save_txt_path}")

    def save_txt_file(self, save_txt_path):
        """텍스트 파일 저장 메서드"""
        label_path = self.controller.model.get_label_path(self.current_image_path)
        scene_rect = self.graphics_scene.sceneRect()
        img_width = scene_rect.width()
        img_height = scene_rect.height()

        with open(save_txt_path, 'w') as f:
            if label_path and os.path.exists(label_path):
                with open(label_path, 'r') as src_file:
                    f.write(src_file.read().strip())
                if self.overlay_items:
                    f.write("\n")

            # 오버레이 이미지에 대한 정보 YOLO 형식으로 저장
            for item in self.overlay_items:
                data = self.controller.get_overlay_data(item)
                if data:
                    f.write(
                        f"{data['class_id']} {data['center_x']:.6f} {data['center_y']:.6f} {data['width']:.6f} {data['height']:.6f}\n")

        print(f"Text file saved: {save_txt_path}")

    def setup_menu(self):
        """메뉴바 설정"""
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        open_folder_action = QAction("Open Folder", self)
        open_folder_action.setShortcut("Ctrl+O")
        open_folder_action.triggered.connect(self.controller.open_folder)
        file_menu.addAction(open_folder_action)

    def setup_toolbar(self):
        """툴바 설정"""
        tool_bar = QToolBar()
        self.addToolBar(tool_bar)

        create_cut_folder_action = QAction("Set Move Path", self)
        create_cut_folder_action.triggered.connect(self.controller.create_cut_folder)
        tool_bar.addAction(create_cut_folder_action)

        move_data_file_action = QAction("Move Data File", self)
        move_data_file_action.setShortcut("Space")
        move_data_file_action.triggered.connect(self.controller.move_data_file)
        tool_bar.addAction(move_data_file_action)

        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.triggered.connect(self.zoom_handler.zoom_in)
        tool_bar.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.triggered.connect(self.zoom_handler.zoom_out)
        tool_bar.addAction(zoom_out_action)

        toggle_labels_action = QAction("Toggle Labels", self)
        toggle_labels_action.triggered.connect(self.controller.toggle_labels)
        tool_bar.addAction(toggle_labels_action)

    def update_tree_view(self, folder_path):
        """트리 뷰 업데이트"""
        self.tree_view.setRootIndex(self.file_model.index(folder_path))

    def display_image(self, image_path):
        """이미지 표시"""
        self.current_image_path = image_path
        image = QImage(image_path)
        self.current_pixmap = QPixmap.fromImage(image)
        self.graphics_scene.clear()
        self.graphics_scene.addPixmap(self.current_pixmap)
        self.graphics_view.fitInView(self.graphics_scene.itemsBoundingRect(), Qt.KeepAspectRatio)
        self.zoom_handler.zoom_level = 1.0
        self.restore_scroll_position()

        label_path = self.controller.model.get_label_path(image_path)
        self.display_label_focused_image(image_path, label_path)

        valid_items = []
        for item in self.overlay_items:
            try:
                _ = item.pos()
                self.graphics_scene.addItem(item)
                valid_items.append(item)
            except RuntimeError:
                pass

        self.overlay_items = valid_items

        try:
            if self.preview_item:
                self.preview_item.hide()
        except RuntimeError:
            self.preview_item = None

    def toggle_labels(self):
        """라벨을 표시하거나 숨기는 메서드"""
        if self.labels_visible:
            self.hide_labels()
        else:
            self.show_labels()
        self.labels_visible = not self.labels_visible

    def show_labels(self):
        """라벨을 표시하는 메서드"""
        label_path = self.controller.model.get_label_path(self.current_image_path)
        if label_path:
            self.display_labels(label_path)

    def hide_labels(self):
        """라벨을 숨기는 메서드"""
        for item in self.label_items:
            if item in self.graphics_scene.items():
                self.graphics_scene.removeItem(item)
        self.label_items.clear()

    def display_labels(self, label_path):
        """레이블 표시"""
        image_rect = self.graphics_scene.itemsBoundingRect()
        image_width = image_rect.width()
        image_height = image_rect.height()

        try:
            with open(label_path, 'r') as file:
                for line in file:
                    parts = line.split()
                    if len(parts) != 5:
                        continue
                    class_id, x_center, y_center, width, height = map(float, parts)
                    rect_x = (x_center - width / 2) * image_width
                    rect_y = (y_center - height / 2) * image_height
                    rect_width = width * image_width
                    rect_height = height * image_height
                    rect = QGraphicsRectItem(QRectF(rect_x, rect_y, rect_width, rect_height))
                    rect.setPen(QPen(QColor(173, 255, 47), 0.5))
                    self.graphics_scene.addItem(rect)
                    self.label_items.append(rect)
        except Exception as e:
            print(f"Error reading label file: {e}")

    def get_current_image_path(self):
        """현재 선택된 이미지 경로 반환"""
        index = self.tree_view.currentIndex()
        return self.file_model.filePath(index)

    def select_next_image(self):
        """다음 이미지 선택"""
        current_index = self.tree_view.currentIndex()
        next_index = self.tree_view.indexBelow(current_index)
        if next_index.isValid():
            self.tree_view.setCurrentIndex(next_index)
            return self.file_model.filePath(next_index)
        return None

    def select_previous_image(self):
        """이전 이미지 선택"""
        current_index = self.tree_view.currentIndex()
        previous_index = self.tree_view.indexAbove(current_index)
        if previous_index.isValid():
            self.tree_view.setCurrentIndex(previous_index)
            return self.file_model.filePath(previous_index)
        return None

    def save_scroll_position(self):
        """스크롤 위치 저장"""
        self.scroll_position = QPoint(
            self.graphics_view.horizontalScrollBar().value(),
            self.graphics_view.verticalScrollBar().value()
        )

    def restore_scroll_position(self):
        """스크롤 위치 복원"""
        self.graphics_view.horizontalScrollBar().setValue(self.scroll_position.x())
        self.graphics_view.verticalScrollBar().setValue(self.scroll_position.y())

    def open_context_menu(self, position):
        """컨텍스트 메뉴 열기"""
        indexes = self.tree_view.selectedIndexes()
        if indexes:
            index = indexes[0]
            menu = QMenu()
            folder_path = QFileInfo(self.file_model.filePath(index)).absolutePath()
            copy_folder_path_action = QAction("Copy Folder Path", self)
            copy_folder_path_action.triggered.connect(lambda: self.copy_to_clipboard(folder_path))
            menu.addAction(copy_folder_path_action)

            copy_file_path_action = QAction("Copy File Path", self)
            copy_file_path_action.triggered.connect(lambda: self.copy_to_clipboard(self.file_model.filePath(index)))
            menu.addAction(copy_file_path_action)

            menu.exec_(QCursor.pos())

    def copy_to_clipboard(self, text):
        """텍스트를 클립보드에 복사"""
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)

    def set_rotation(self, angle):
        """회전 각도 설정"""
        self.current_rotation = angle

    def add_overlay_image(self, pos):
        """오버레이 이미지 추가"""
        if self.selected_overlay_images:
            overlay_pixmap = self.selected_overlay_images[self.current_overlay_index]

            # 회전 각도 결정
            if self.image_list_window.random_rotation_radio.isChecked():
                rotation = random.uniform(0, 360)
                self.image_list_window.set_rotation_input(rotation)
            elif self.image_list_window.fixed_rotation_radio.isChecked():
                try:
                    rotation = float(self.image_list_window.rotation_input.text())
                except ValueError:
                    rotation = 0
            elif self.image_list_window.direction_light_radio.isChecked():
                rotation = self.calculate_direction_light_rotation(pos)

            # 회전 적용
            transform = QTransform().rotate(rotation)
            rotated_pixmap = overlay_pixmap.transformed(transform, Qt.SmoothTransformation)

            overlay_item = QGraphicsPixmapItem(rotated_pixmap)
            overlay_item.setPos(pos - QPointF(rotated_pixmap.width() / 2, rotated_pixmap.height() / 2))

            original_image_path = self.image_list_window.image_widgets[self.current_overlay_index].image_path
            overlay_item.setData(0, original_image_path)
            overlay_item.setData(1, rotation)

            # 회전된 바운딩 박스 계산
            rect = overlay_item.boundingRect()
            pos = overlay_item.pos()
            center_x = (pos.x() + rect.width() / 2) / self.graphics_scene.width()
            center_y = (pos.y() + rect.height() / 2) / self.graphics_scene.height()
            width = rect.width() / self.graphics_scene.width()
            height = rect.height() / self.graphics_scene.height()

            class_id = "3"  # 기본값
            self.controller.save_overlay_data(overlay_item, class_id, center_x, center_y, width, height, rotation)

            self.graphics_scene.addItem(overlay_item)
            self.overlay_items.append(overlay_item)

    def calculate_direction_light_rotation(self, pos):
        """방향성 조명 회전 각도 계산"""
        overlay_width = self.selected_overlay_images[self.current_overlay_index].width()
        overlay_height = self.selected_overlay_images[self.current_overlay_index].height()

        x = int(pos.x() - overlay_width / 2)
        y = int(pos.y() - overlay_height / 2)

        background_region = self.current_pixmap.toImage().copy(x, y, overlay_width, overlay_height)

        background_region_cv = self.qimage_to_cv2(background_region)
        main_direction, _, _ = get_main_direction(background_region_cv)
        return np.degrees(main_direction)

    def qimage_to_cv2(self, qimage):
        """QImage를 OpenCV 형식으로 변환"""
        qimage = qimage.convertToFormat(QImage.Format.Format_RGBA8888)
        width = qimage.width()
        height = qimage.height()
        ptr = qimage.bits()
        arr = np.array(ptr).reshape(height, width, 4)
        return arr[..., :3][..., ::-1]

    def keyPressEvent(self, event):
        """키 프레스 이벤트 처리"""
        if event.key() == Qt.Key_Tab:
            # Tab 키를 눌러 다음 오버레이 이미지 선택
            if self.selected_overlay_images:
                self.current_overlay_index = (self.current_overlay_index + 1) % len(self.selected_overlay_images)
        elif event.key() == Qt.Key_Backtab:
            # Shift+Tab 키를 눌러 이전 오버레이 이미지 선택
            if self.selected_overlay_images:
                self.current_overlay_index = (self.current_overlay_index - 1) % len(self.selected_overlay_images)

        if event.key() == Qt.Key_Control:
            if self.cursor_visible:
                QApplication.setOverrideCursor(Qt.BlankCursor)
                self.cursor_visible = False 

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """키 눌렸을 때 이벤트"""
        if event.key() == Qt.Key_Control:
            if not self.cursor_visible:
                QApplication.restoreOverrideCursor()
                self.cursor_visible = True 
        super().keyReleaseEvent(event)

    def leaveEvent(self, event): 
        """마우스가 위젯을 벗어날 때 이벤트"""
        if not self.cursor_visible:
            QApplication.restoreOverrideCursor()
            self.cursor_visible = True
        super().leaveEvent(event) 

    def mousePressEvent(self, event):
        """마우스 프레스 이벤트"""
        if event.button() == Qt.LeftButton:
            self.pan_handler.start_pan(event.pos())
        elif event.button() == Qt.RightButton and QApplication.keyboardModifiers() == Qt.ControlModifier:
            if self.selected_overlay_images:
                pos = self.graphics_view.mapToScene(self.graphics_view.mapFromGlobal(event.globalPos()))
                self.add_overlay_image(pos)
                if self.preview_item:
                    self.preview_item.hide()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """마우스 릴리스 이벤트"""
        if event.button() == Qt.LeftButton:
            self.pan_handler.stop_pan()
        elif event.button() == Qt.RightButton and QApplication.keyboardModifiers() == Qt.ControlModifier:
            if self.preview_item:
                self.preview_item.hide()
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        """마우스 이동 이벤트 처리"""
        self.pan_handler.pan(event.pos())
        super().mouseMoveEvent(event)

    def update_zoom(self):
        """새 뷰어 확대 비율 업데이트"""
        if hasattr(self, 'current_image_path') and self.current_image_path:
            self.display_label_focused_image(self.current_image_path,
                                             self.controller.model.get_label_path(self.current_image_path))

    def display_label_focused_image(self, image_path, label_path=None):
        """라벨 이미지 중심 미리보기"""
        try:
            image = QImage(image_path)
            if image.isNull():
                print(f"Failed to load image: {image_path}")
                return

            if label_path:
                image_width = image.width()
                image_height = image.height()

                zoom_spinboxes = [self.zoom_spinbox1, self.zoom_spinbox2]
                label_views = [self.label_view1, self.label_view2]

                for zoom_spinbox, label_view in zip(zoom_spinboxes, label_views):
                    zoom_factor = zoom_spinbox.value() / 100
                    scaled_image = image.scaled(image_width * zoom_factor, image_height * zoom_factor,
                                                Qt.KeepAspectRatio)

                    if label_path:
                        with open(label_path, 'r') as file:
                            for line in file:
                                parts = line.split()
                                if len(parts) != 5:
                                    continue
                                _, x_center, y_center, width, height = map(float, parts)

                                center_x = x_center * image_width
                                center_y = y_center * image_height

                                crop_x = max(0, int(center_x * zoom_factor - 300))
                                crop_y = max(0, int(center_y * zoom_factor - 300))
                                crop_width = min(600, scaled_image.width() - crop_x)
                                crop_height = min(600, scaled_image.height() - crop_y)

                                cropped_image = scaled_image.copy(crop_x, crop_y, crop_width, crop_height)
                                label_view.setPixmap(QPixmap.fromImage(cropped_image))
                                label_view.setScaledContents(True)
                                break
                    else:
                        label_view.setPixmap(QPixmap.fromImage(scaled_image))
                        label_view.setScaledContents(True)
        except Exception as e:
            print(f"Error displaying label-focused image: {e}")

    def eventFilter(self, source, event):
        """이벤트 조건 필터 처리"""
        if source == self.graphics_view.viewport():
            if event.type() == QEvent.MouseMove and QApplication.keyboardModifiers() == Qt.ControlModifier:
                pos = self.graphics_view.mapToScene(event.pos())
                self.update_preview(pos)
                return True
        return super().eventFilter(source, event)

    def update_preview(self, pos):
        """미리보기 업데이트"""
        if self.selected_overlay_images:
            try:
                if self.preview_item is None or not self.graphics_scene.items().count(self.preview_item):
                    self.preview_item = QGraphicsPixmapItem()
                    self.graphics_scene.addItem(self.preview_item)

                overlay_pixmap = self.selected_overlay_images[self.current_overlay_index]

                # 회전 각도 결정
                if self.image_list_window.random_rotation_radio.isChecked():
                    rotation = random.uniform(0, 360)
                elif self.image_list_window.fixed_rotation_radio.isChecked():
                    try:
                        rotation = float(self.image_list_window.rotation_input.text())
                    except ValueError:
                        rotation = 0
                elif self.image_list_window.direction_light_radio.isChecked():
                    rotation = self.calculate_direction_light_rotation(pos)

                # 회전 적용
                transform = QTransform().rotate(rotation)
                rotated_pixmap = overlay_pixmap.transformed(transform, Qt.SmoothTransformation)

                self.preview_item.setPixmap(rotated_pixmap)
                self.preview_item.setPos(pos - QPointF(rotated_pixmap.width() / 2, rotated_pixmap.height() / 2))
                self.preview_item.setOpacity(1.0)
                self.preview_item.show()
            except RuntimeError:
                # preview_item이 이미 삭제되었다면 None으로 설정
                self.preview_item = None
        elif self.preview_item:
            try:
                self.preview_item.hide()
            except RuntimeError:
                self.preview_item = None

def get_main_direction(image):
    """주요 방향 계산"""
    # Sobel 연산자를 사용한 에지 검출
    sobel_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=5)
    sobel_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=5)

    # 방향 계산
    magnitude = np.sqrt(sobel_x ** 2 + sobel_y ** 2)
    direction = np.arctan2(sobel_y, sobel_x)

    # 히스토그램을 통해 주요 방향 찾기
    hist, bin_edges = np.histogram(direction, bins=180, range=(-np.pi, np.pi))
    main_direction = bin_edges[np.argmax(hist)]

    return main_direction, magnitude, direction