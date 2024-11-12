import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QFileDialog, QGraphicsView, QGraphicsScene,
                               QGraphicsRectItem, QVBoxLayout, QTreeView, QFileSystemModel,
                               QMenuBar, QToolBar, QWidget, QSplitter, QSizePolicy, QMenu)
from PySide6.QtGui import QImage, QPixmap, QPen, QAction, QColor, QKeyEvent, QWheelEvent, QCursor, QGuiApplication
from PySide6.QtCore import Qt, QDir, QModelIndex, QRectF, QDirIterator, QFileInfo, QFile, QPoint, QObject

class ImageViewerController(QObject):
    def __init__(self):
        super().__init__()
        self.model = ImageViewerModel()
        self.view = ImageViewerView(self)
        self.view.tree_view.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.labels_visible = True

    def on_selection_changed(self, selected, deselected):
        indexes = self.view.tree_view.selectionModel().selectedIndexes()
        if indexes:
            self.load_image(indexes[0])

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(None, "Select Folder")
        if folder_path:
            self.model.set_folder(folder_path)
            self.view.update_tree_view(folder_path)
            first_index = self.model.get_first_image_index(folder_path)
            if first_index.isValid():
                self.load_image(first_index)

    def load_image(self, index: QModelIndex):
        self.view.save_scroll_position()
        image_path = self.model.get_image_path(index)
        if image_path:
            self.view.display_image(image_path)
            if self.labels_visible:
                label_path = self.model.get_label_path(image_path)
                if label_path:
                    self.view.display_labels(label_path)
        self.view.restore_scroll_position()

    def create_cut_folder(self):
        if not self.model.cut_folder_exists():
            self.model.create_cut_folder()

    def move_data_file(self):
        self.create_cut_folder()
        selected_image = self.view.get_current_image_path()
        if selected_image:
            self.view.save_scroll_position()
            self.model.move_data_file(selected_image)
            next_index = self.view.select_next_image()
            if next_index.isValid():
                self.load_image(next_index)

    def zoom_in(self):
        self.view.zoom_in()

    def zoom_out(self):
        self.view.zoom_out()

    def toggle_labels(self):
        self.labels_visible = not self.labels_visible
        current_image_path = self.view.get_current_image_path()
        if current_image_path:
            self.view.display_image(current_image_path)
            if self.labels_visible:
                label_path = self.model.get_label_path(current_image_path)
                if label_path:
                    self.view.display_labels(label_path)

class ImageViewerModel:
    def __init__(self):
        self.current_folder = None
        self.cut_folder = None
        self.file_model = QFileSystemModel()

    def set_folder(self, folder_path):
        self.current_folder = folder_path

    def get_first_image_index(self, folder_path):
        iterator = QDirIterator(folder_path, ["*.png", "*.jpg", "*.jpeg"], QDir.Files, QDirIterator.Subdirectories)
        while iterator.hasNext():
            return self.file_model.index(iterator.next())
        return QModelIndex()

    def get_image_path(self, index: QModelIndex):
        if self.file_model.isDir(index):
            return None
        file_path = self.file_model.filePath(index)
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            return file_path
        return None

    def get_label_path(self, image_path):
        label_path = image_path.rsplit('.', 1)[0] + ".txt"
        if QFileInfo.exists(label_path):
            return label_path
        return None

    def create_cut_folder(self):
        if self.current_folder:
            self.cut_folder = f"{self.current_folder}_cut"
            QDir().mkpath(self.cut_folder)

    def cut_folder_exists(self):
        if self.current_folder:
            cut_folder_path = f"{self.current_folder}_cut"
            return QDir(cut_folder_path).exists()
        return False

    def move_data_file(self, image_path):
        if not self.cut_folder:
            self.create_cut_folder()
        if not image_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            return  # 이미지 파일이 아닌 경우 아무 작업도 하지 않음
        relative_path = QDir(self.current_folder).relativeFilePath(image_path)
        cut_image_path = QDir(self.cut_folder).filePath(relative_path)
        QDir().mkpath(QFileInfo(cut_image_path).absolutePath())
        QFile.rename(image_path, cut_image_path)

        label_path = image_path.rsplit('.', 1)[0] + ".txt"
        if QFileInfo.exists(label_path):
            cut_label_path = cut_image_path.rsplit('.', 1)[0] + ".txt"
            QFile.rename(label_path, cut_label_path)

class ImageViewerView(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Image Viewer")
        self.is_panning = False
        self.last_pan_point = QPoint()
        self.zoom_level = 1.0
        self.current_image_rect = None
        self.scroll_position = QPoint()

        # Central Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Splitter for layout
        splitter = QSplitter(Qt.Horizontal)
        self.layout.addWidget(splitter)

        # Graphics View for displaying images
        self.graphics_view = QGraphicsView()
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        splitter.addWidget(self.graphics_view)

        # Tree View for displaying folder structure
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath("")
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.file_model)
        self.tree_view.setRootIsDecorated(False)
        self.tree_view.setSortingEnabled(True)
        self.tree_view.sortByColumn(0, Qt.AscendingOrder)
        self.tree_view.hideColumn(1)  # Hide size column
        self.tree_view.hideColumn(2)  # Hide type column
        self.tree_view.hideColumn(3)  # Hide date modified column
        splitter.addWidget(self.tree_view)
        splitter.setSizes([int(self.width() * 0.9), int(self.width() * 0.1)])  # 탐색기 창의 초기 가로 값을 전체 창의 10%로 설정

        # Filter to show only image files
        self.file_model.setNameFilters(["*.png", "*.jpg", "*.jpeg"])
        self.file_model.setNameFilterDisables(False)

        # Menu Bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        open_folder_action = QAction("Open Folder", self)
        open_folder_action.setShortcut("Ctrl+O")
        open_folder_action.triggered.connect(self.controller.open_folder)
        file_menu.addAction(open_folder_action)

        # Tool Bar
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
        zoom_in_action.triggered.connect(self.controller.zoom_in)
        tool_bar.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.triggered.connect(self.controller.zoom_out)
        tool_bar.addAction(zoom_out_action)

        toggle_labels_action = QAction("Toggle Labels", self)
        toggle_labels_action.triggered.connect(self.controller.toggle_labels)
        tool_bar.addAction(toggle_labels_action)

        self.graphics_view.setDragMode(QGraphicsView.ScrollHandDrag)

        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.open_context_menu)

        self.show()

    def update_tree_view(self, folder_path):
        self.tree_view.setRootIndex(self.file_model.index(folder_path))

    def display_image(self, image_path):
        self.current_image_path = image_path
        image = QImage(image_path)
        self.current_pixmap = QPixmap.fromImage(image)
        self.graphics_scene.clear()
        self.graphics_scene.addPixmap(self.current_pixmap)

        if self.current_image_rect:
            self.graphics_view.setSceneRect(self.current_image_rect)
        else:
            self.graphics_view.fitInView(self.graphics_scene.itemsBoundingRect(), Qt.KeepAspectRatio)

        self.graphics_view.resetTransform()
        self.graphics_view.scale(self.zoom_level, self.zoom_level)
        self.restore_scroll_position()  # 스크롤 위치를 복원합니다.

    def display_labels(self, label_path):
        print(f"Displaying labels from: {label_path}")  # Debug print
        image_rect = self.graphics_scene.itemsBoundingRect()
        image_width = image_rect.width()
        image_height = image_rect.height()

        try:
            with open(label_path, 'r') as file:
                for line in file:
                    parts = line.split()
                    if len(parts) != 5:
                        print(f"Skipping invalid line: {line}")  # Debug print
                        continue
                    class_id, x_center, y_center, width, height = map(float, parts)
                    rect_x = (x_center - width / 2) * image_width
                    rect_y = (y_center - height / 2) * image_height
                    rect_width = width * image_width
                    rect_height = height * image_height
                    rect = QGraphicsRectItem(QRectF(rect_x, rect_y, rect_width, rect_height))
                    rect.setPen(QPen(QColor(173, 255, 47), 0.5))  # 형광 연두색 및 두께 조정
                    self.graphics_scene.addItem(rect)
                    print(f"Added label: {rect_x}, {rect_y}, {rect_width}, {rect_height}")  # Debug print
        except Exception as e:
            print(f"Error reading label file: {e}")  # Debug print

    def get_current_image_path(self):
        index = self.tree_view.currentIndex()
        return self.file_model.filePath(index)

    def zoom_in(self):
        self.zoom_level *= 1.2
        self.graphics_view.scale(1.2, 1.2)

    def zoom_out(self):
        self.zoom_level /= 1.2
        self.graphics_view.scale(1 / 1.2, 1 / 1.2)

    def select_next_image(self):
        current_index = self.tree_view.currentIndex()
        next_index = self.tree_view.indexBelow(current_index)
        if next_index.isValid():
            self.tree_view.setCurrentIndex(next_index)
            self.controller.load_image(next_index)
        return next_index

    def select_previous_image(self):
        current_index = self.tree_view.currentIndex()
        previous_index = self.tree_view.indexAbove(current_index)
        if previous_index.isValid():
            self.tree_view.setCurrentIndex(previous_index)
            self.controller.load_image(previous_index)
        return previous_index

    def wheelEvent(self, event: QWheelEvent):
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            super().wheelEvent(event)

    def save_scroll_position(self):
        self.scroll_position = QPoint(
            self.graphics_view.horizontalScrollBar().value(),
            self.graphics_view.verticalScrollBar().value()
        )

    def restore_scroll_position(self):
        self.graphics_view.horizontalScrollBar().setValue(self.scroll_position.x())
        self.graphics_view.verticalScrollBar().setValue(self.scroll_position.y())

    def open_context_menu(self, position):
        indexes = self.tree_view.selectedIndexes()
        if indexes:
            index = indexes[0]
            source_index = self.proxy_model.mapToSource(index)
            menu = QMenu()
            folder_path = QFileInfo(self.file_model.filePath(source_index)).absolutePath()
            copy_folder_path_action = QAction("Copy Folder Path", self)
            copy_folder_path_action.triggered.connect(lambda: self.copy_to_clipboard(folder_path))
            menu.addAction(copy_folder_path_action)

            copy_file_path_action = QAction("Copy File Path", self)
            copy_file_path_action.triggered.connect(lambda: self.copy_to_clipboard(self.file_model.filePath(source_index)))
            menu.addAction(copy_file_path_action)

            menu.exec_(QCursor.pos())

    def copy_to_clipboard(self, text):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Space:
            self.controller.move_data_file()
        elif event.key() in [Qt.Key_Right, Qt.Key_D, Qt.Key_Up, Qt.Key_W, Qt.Key_Left, Qt.Key_A, Qt.Key_Down, Qt.Key_S]:
            super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Space:
            self.is_panning = False
            self.graphics_view.setCursor(Qt.ArrowCursor)
        else:
            super().keyReleaseEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and QApplication.keyboardModifiers() != Qt.ControlModifier:
            self.last_pan_point = event.pos()
            self.is_panning = True
            self.graphics_view.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_panning = False
            self.graphics_view.setCursor(Qt.OpenHandCursor if self.is_panning else Qt.ArrowCursor)
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_panning and not self.last_pan_point.isNull():
            delta = self.last_pan_point - event.pos()
            self.graphics_view.horizontalScrollBar().setValue(
                self.graphics_view.horizontalScrollBar().value() + delta.x())
            self.graphics_view.verticalScrollBar().setValue(
                self.graphics_view.verticalScrollBar().value() + delta.y())
            self.last_pan_point = event.pos()
        super().mouseMoveEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = ImageViewerController()
    controller.view.show()
    sys.exit(app.exec())