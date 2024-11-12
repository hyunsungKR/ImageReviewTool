import os

from PySide6.QtWidgets import QFileSystemModel
from PySide6.QtCore import QDir, QModelIndex, QDirIterator, QFileInfo, QFile, QObject, Signal


class ImageViewerModel(QObject):
    # 이미지 변경 시그널
    image_changed = Signal(str)
    # 레이블 변경 시그널
    labels_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.current_folder = None
        self.cut_folder = None
        self.file_model = QFileSystemModel()
        self.folder_path = ""  # 이미지 루트 디렉토리 추가

    def set_additional_label_dir(self, dir_path):
        """Set the directory path for additional labels"""
        self.additional_label_dir = dir_path

    def get_additional_label_path(self, image_path):
        """Get the additional label path for the given image"""
        if self.additional_label_dir is None:
            return None
        image_filename = os.path.basename(image_path)
        base_name, _ = os.path.splitext(image_filename)
        label_filename = base_name + '.txt'
        label_path = os.path.join(self.additional_label_dir, label_filename)
        if os.path.exists(label_path):
            return label_path
        else:
            return None

    def set_folder(self, folder_path):
        """현재 폴더를 설정하고 첫 번째 이미지를 로드"""
        self.folder_path = folder_path  # self.folder_path 설정 추가
        self.current_folder = folder_path
        self.image_changed.emit(self.get_first_image_path(folder_path))

    def get_first_image_path(self, folder_path):
        '''
        폴더를 선택하면 첫번째 이미지 경로를 반환하고 , 파일을 선택하면 해당파일의 경로를 반환한다.
        :param folder_path:
        :return:
        '''
        iterator = QDirIterator(folder_path, ["*.png", "*.jpg", "*.jpeg"], QDir.Files, QDirIterator.Subdirectories)
        if iterator.hasNext():
            return iterator.next()
        return None

    def get_image_path(self, index: QModelIndex):
        """주어진 인덱스의 이미지 파일 경로를 반환"""
        if self.file_model.isDir(index):
            folder_path = self.file_model.filePath(index)
            return self.get_first_image_path(folder_path)
        file_path = self.file_model.filePath(index)
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            return file_path
        return None

    def get_label_path(self, image_path):
        """이미지 파일에 대응하는 레이블 파일 경로를 반환"""
        label_path = image_path.rsplit('.', 1)[0] + ".txt"
        if QFileInfo.exists(label_path):
            self.labels_changed.emit(label_path)
            return label_path
        return None

    def create_cut_folder(self):
        """잘라내기 폴더 생성"""
        if self.current_folder:
            self.cut_folder = f"{self.current_folder}_cut"
            QDir().mkpath(self.cut_folder)

    def cut_folder_exists(self):
        """잘라내기 폴더 존재 여부 확인"""
        if self.current_folder:
            cut_folder_path = f"{self.current_folder}_cut"
            return QDir(cut_folder_path).exists()
        return False

    def move_data_file(self, image_path):
        """이미지 파일과 관련 레이블 파일을 잘라내기 폴더로 이동"""
        if not self.cut_folder:
            self.create_cut_folder()
        if not image_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            return
        relative_path = QDir(self.current_folder).relativeFilePath(image_path)
        cut_image_path = QDir(self.cut_folder).filePath(relative_path)
        QDir().mkpath(QFileInfo(cut_image_path).absolutePath())
        QFile.rename(image_path, cut_image_path)

        label_path = image_path.rsplit('.', 1)[0] + ".txt"
        if QFileInfo.exists(label_path):
            cut_label_path = cut_image_path.rsplit('.', 1)[0] + ".txt"
            QFile.rename(label_path, cut_label_path)

        self.image_changed.emit(self.get_next_image_path(image_path))

    def get_next_image_path(self, current_image_path):
        """현재 이미지의 다음 이미지 경로를 반환"""
        current_dir = QFileInfo(current_image_path).absolutePath()
        iterator = QDirIterator(current_dir, ["*.png", "*.jpg", "*.jpeg"], QDir.Files)
        found_current = False
        while iterator.hasNext():
            next_path = iterator.next()
            if found_current:
                return next_path
            if next_path == current_image_path:
                found_current = True
        return None

