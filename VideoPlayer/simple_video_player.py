import sys
import os
import cv2
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QFileDialog
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import QTimer, Qt


class SimpleVideoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Video Player")
        self.setGeometry(100, 100, 800, 600)

        # 중앙 위젯 및 레이아웃 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 폴더 선택 버튼 생성
        self.select_folder_button = QPushButton("Select Folder")
        self.select_folder_button.clicked.connect(self.select_folder)
        layout.addWidget(self.select_folder_button)

        # 비디오를 표시할 레이블 생성
        self.video_label = QLabel()
        layout.addWidget(self.video_label)

        # 비디오 캡처 객체 및 타이머 초기화
        self.video_capture = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        # 현재 재생 중인 비디오 파일 목록 및 인덱스
        self.video_files = []
        self.current_video_index = 0

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.video_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path)
                                if f.lower().endswith(('.mp4', '.avi', '.mov'))]
            if self.video_files:
                self.current_video_index = 0
                self.start_video(self.video_files[0])
            else:
                self.video_label.setText("No video files found in the selected folder.")

    def start_video(self, video_path):
        if self.video_capture:
            self.video_capture.release()
        self.video_capture = cv2.VideoCapture(video_path)
        self.timer.start(33)  # 약 30 FPS

    def update_frame(self):
        if self.video_capture is None:
            return

        ret, frame = self.video_capture.read()
        if ret:
            # OpenCV BGR 이미지를 RGB로 변환
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w

            # QImage 생성
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)

            # QPixmap으로 변환하여 레이블에 표시
            pixmap = QPixmap.fromImage(qt_image)
            self.video_label.setPixmap(
                pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            # 현재 비디오가 끝나면 다음 비디오로 넘어가기
            self.current_video_index = (self.current_video_index + 1) % len(self.video_files)
            self.start_video(self.video_files[self.current_video_index])

    def closeEvent(self, event):
        # 윈도우가 닫힐 때 리소스 정리
        if self.video_capture:
            self.video_capture.release()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = SimpleVideoPlayer()
    player.show()
    sys.exit(app.exec())