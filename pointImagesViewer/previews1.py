import os
import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QLineEdit, QPushButton,
    QSizePolicy, QFileDialog, QSplitter, QTableWidget, QTableWidgetItem,
    QAbstractScrollArea, QAbstractItemView, QScrollArea, QGridLayout
)
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt


class ImageViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("이미지 뷰어")
        self.resize(1000, 1000)

        # 이미지 크기 기본값
        self.image_size = 100

        # 루트 폴더 설정
        self.root_folder = ''  # 초기에는 빈 문자열

        # 메인 레이아웃 (수직 레이아웃)
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # QSplitter를 사용하여 좌우로 분할
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # 좌측 위젯 (폴더 리스트 및 설정)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # 이미지 크기 입력
        size_layout = QHBoxLayout()
        size_label = QLabel("이미지 최대 크기:")
        size_layout.addWidget(size_label)

        self.size_input = QLineEdit(str(self.image_size))
        self.size_input.setFixedWidth(50)
        size_layout.addWidget(self.size_input)

        size_button = QPushButton("적용")
        size_button.clicked.connect(self.update_image_size)
        size_layout.addWidget(size_button)

        left_layout.addLayout(size_layout)

        # 폴더 간격 입력
        spacing_layout = QHBoxLayout()
        spacing_label = QLabel("폴더 간격:")
        spacing_layout.addWidget(spacing_label)

        self.spacing_input = QLineEdit("0")
        self.spacing_input.setFixedWidth(50)
        spacing_layout.addWidget(self.spacing_input)

        spacing_button = QPushButton("적용")
        spacing_button.clicked.connect(self.update_folder_spacing)
        spacing_layout.addWidget(spacing_button)

        left_layout.addLayout(spacing_layout)

        # 폴더 선택 버튼
        folder_button = QPushButton("폴더 선택")
        folder_button.clicked.connect(self.select_root_folder)
        left_layout.addWidget(folder_button)

        # 폴더 리스트
        self.folder_list = QListWidget()
        self.folder_list.itemClicked.connect(self.on_folder_select)
        left_layout.addWidget(self.folder_list)

        # 좌측 위젯을 splitter에 추가하고 기본 너비를 300px로 설정
        splitter.addWidget(left_widget)
        left_widget.setMinimumWidth(100)
        left_widget.setMaximumWidth(300)
        left_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        splitter.setSizes([300, 700])  # 좌측 300px, 우측 나머지

        # 우측 위젯 (이미지 뷰어)
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout(self.right_widget)
        splitter.addWidget(self.right_widget)

        # 테이블 위젯 (기본 뷰)
        self.table_widget = QTableWidget()
        self.table_widget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)  # 행 전체 선택
        self.right_layout.addWidget(self.table_widget)

        # 스크롤 영역 (폴더 선택 시 이미지 그리드 뷰)
        self.scroll_area = QScrollArea()
        self.scroll_area_widget = QWidget()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_area_widget)
        self.grid_layout = QGridLayout(self.scroll_area_widget)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scroll_area.hide()  # 초기에는 숨김
        self.right_layout.addWidget(self.scroll_area)

    def select_root_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "폴더 선택", "")
        if folder:
            self.root_folder = folder
            self.load_folders()
            self.display_all_folders()

    def update_image_size(self):
        try:
            size = int(self.size_input.text())
            if size >= 0:
                self.image_size = size
                # 이미지 크기 변경 후 다시 로드
                if self.folder_list.currentItem():
                    self.on_folder_select(self.folder_list.currentItem())
                else:
                    self.display_all_folders()
        except ValueError:
            pass  # 숫자가 아닐 경우 무시

    def update_folder_spacing(self):
        try:
            spacing = int(self.spacing_input.text())
            if spacing >= 0:
                self.folder_list.setSpacing(spacing)
        except ValueError:
            pass  # 숫자가 아닐 경우 무시

    def clear_table(self):
        self.table_widget.clear()
        self.table_widget.setRowCount(0)
        self.table_widget.setColumnCount(0)

    def clear_grid_layout(self):
        # 그리드 레이아웃 초기화
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def load_folders(self):
        self.folder_list.clear()
        self.folders_info = []
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')

        # 'a' 폴더 항목 추가
        a_item = QListWidgetItem(os.path.basename(self.root_folder))
        a_item.setData(Qt.UserRole, 'root')
        self.folder_list.addItem(a_item)

        # 첫 번째 하위 폴더만 탐색
        for folder_name in sorted(os.listdir(self.root_folder)):
            folder_path = os.path.join(self.root_folder, folder_name)
            if os.path.isdir(folder_path):
                images = []
                # os.walk를 사용하여 하위 폴더까지 모든 파일 탐색
                for root, dirs, files in os.walk(folder_path):
                    images.extend(
                        [os.path.join(root, f) for f in sorted(files) if f.lower().endswith(image_extensions)])

                image_count = len(images)
                preview_image = images[0] if image_count > 0 else None
                folder_info = {
                    'name': folder_name,
                    'path': folder_path,
                    'images': images,
                    'count': image_count,
                    'preview': preview_image
                }
                self.folders_info.append(folder_info)

                # 폴더 리스트 아이템 생성
                item_text = f"{folder_name} ({image_count}장)"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, folder_info)
                if preview_image:
                    img_path = preview_image
                    pixmap = QPixmap(img_path)
                    if pixmap.width() > 50 or pixmap.height() > 50:
                        pixmap = pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    if not pixmap.isNull():  # 이미지가 제대로 로드되었는지 확인
                        item.setIcon(QIcon(pixmap))
                self.folder_list.addItem(item)

    def on_folder_select(self, item):
        role = item.data(Qt.UserRole)
        if role == 'root':
            self.display_all_folders()
        else:
            self.display_folder_images(role)

    def display_all_folders(self):
        # 테이블 뷰 표시
        self.scroll_area.hide()
        self.table_widget.show()

        # 테이블 초기화
        self.clear_table()

        if not self.folders_info:
            return

        # 최대 이미지 수 계산
        max_image_count = max(folder_info['count'] for folder_info in self.folders_info)
        total_columns = 4 + max_image_count  # 인덱스 컬럼 추가

        # 테이블 설정
        self.table_widget.setRowCount(len(self.folders_info))
        self.table_widget.setColumnCount(total_columns)
        headers = ["Index", "Folder Name", "Actual Size", "Number of Files"] + [str(i+1) for i in range(max_image_count)]
        self.table_widget.setHorizontalHeaderLabels(headers)
        self.table_widget.verticalHeader().setVisible(False)

        for row_idx, folder_info in enumerate(self.folders_info):
            # 인덱스 번호
            index_item = QTableWidgetItem(str(row_idx + 1))
            index_item.setTextAlignment(Qt.AlignCenter)
            self.table_widget.setItem(row_idx, 0, index_item)

            # 폴더 이름
            folder_name_item = QTableWidgetItem(folder_info['name'])
            self.table_widget.setItem(row_idx, 1, folder_name_item)

            # 첫 번째 이미지의 크기 (픽셀)
            if folder_info['images']:
                first_image_path = os.path.join(folder_info['path'], folder_info['images'][0])
                pixmap = QPixmap(first_image_path)
                width = pixmap.width()
                height = pixmap.height()
                size_str = f"{width} x {height} px"
            else:
                size_str = "N/A"
            size_item = QTableWidgetItem(size_str)
            self.table_widget.setItem(row_idx, 2, size_item)

            # 파일 개수
            count_item = QTableWidgetItem(str(folder_info['count']))
            self.table_widget.setItem(row_idx, 3, count_item)

            # 이미지 추가
            for col_idx, img_name in enumerate(folder_info['images']):
                img_path = os.path.join(folder_info['path'], img_name)
                pixmap = QPixmap(img_path)
                if self.image_size > 0:
                    pixmap = pixmap.scaled(self.image_size, self.image_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                label = QLabel()
                label.setPixmap(pixmap)
                label.setAlignment(Qt.AlignCenter)
                label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
                label.setScaledContents(False)
                self.table_widget.setCellWidget(row_idx, col_idx + 4, label)
                # 셀 크기 조절
                self.table_widget.setColumnWidth(col_idx + 4, pixmap.width())
            # 행 높이 조절
            max_height = max([self.table_widget.cellWidget(row_idx, col + 4).pixmap().height()
                              for col in range(len(folder_info['images']))]) if folder_info['images'] else 30
            self.table_widget.setRowHeight(row_idx, max_height)

    def display_folder_images(self, folder_info):
        # 그리드 뷰 표시
        self.table_widget.hide()
        self.scroll_area.show()

        # 그리드 레이아웃 초기화
        self.clear_grid_layout()

        # 폴더 정보 표시
        info_label = QLabel(f"폴더 이름: {folder_info['name']}    이미지 개수: {folder_info['count']}장")
        info_label.setStyleSheet("font-weight: bold; font-size: 16px; margin: 10px;")
        self.grid_layout.addWidget(info_label, 0, 0, 1, -1)  # 첫 번째 행 전체 차지

        images = folder_info['images']
        if images:
            col_count = self.calculate_columns()
            row = 1
            col = 0
            for img_name in images:
                img_path = os.path.join(folder_info['path'], img_name)
                pixmap = QPixmap(img_path)
                if self.image_size > 0:
                    pixmap = pixmap.scaled(self.image_size, self.image_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                label = QLabel()
                label.setPixmap(pixmap)
                label.setAlignment(Qt.AlignCenter)
                label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
                label.setScaledContents(False)
                self.grid_layout.addWidget(label, row, col)
                col += 1
                if col >= col_count:
                    col = 0
                    row += 1
        else:
            no_image_label = QLabel("이미지가 없습니다.")
            self.grid_layout.addWidget(no_image_label, 1, 0)

    def calculate_columns(self):
        # 윈도우 크기에 따라 열 수 계산
        total_width = self.scroll_area.width()
        if self.image_size > 0:
            image_width = self.image_size
        else:
            # 임의로 100px로 설정
            image_width = 100
        col_count = max(1, total_width // (image_width + 10))  # 여백 고려
        return col_count

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 폴더 선택 시 그리드 레이아웃 재조정
        if self.scroll_area.isVisible() and hasattr(self, 'grid_layout'):
            self.display_folder_images(self.folder_list.currentItem().data(Qt.UserRole))

    def human_readable_size(self, size, decimal_places=2):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.{decimal_places}f} {unit}"
            size /= 1024.0
        return f"{size:.{decimal_places}f} PB"


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = ImageViewer()
    viewer.show()
    sys.exit(app.exec())
