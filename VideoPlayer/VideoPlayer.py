import sys
import cv2
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QGraphicsView, QGraphicsScene
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt, QTimer, QPointF


class VideoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Player with Zoom")
        self.setGeometry(100, 100, 800, 600)

        # 그래픽스 뷰 및 씬 설정
        self.graphics_view = QGraphicsView(self)
        self.setCentralWidget(self.graphics_view)
        self.scene = QGraphicsScene(self)
        self.graphics_view.setScene(self.scene)

        # 비디오 관련 변수 초기화
        self.video_capture = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        # 줌 관련 변수 초기화
        self.zoom_factor = 1.0
        self.zoom_step = 0.1  # 한 번의 휠 움직임에 대한 줌 변화량

        # 비디오 로드
        self.load_video()

    def load_video(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov)")
        if file_name:
            self.video_capture = cv2.VideoCapture(file_name)
            self.timer.start(33)  # 약 30 FPS

    def update_frame(self):
        ret, frame = self.video_capture.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)

            # 기존 항목 제거 및 새 프레임 추가
            self.scene.clear()
            self.scene.addPixmap(pixmap)

            # 현재 줌 레벨 유지
            self.graphics_view.setTransform(self.graphics_view.transform())
        else:
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def wheelEvent(self, event):
        # 마우스 휠 이벤트 처리
        zoom_in = event.angleDelta().y() > 0

        # 줌 팩터 계산
        if zoom_in:
            self.zoom_factor = 1 + self.zoom_step
        else:
            self.zoom_factor = 1 / (1 + self.zoom_step)

        # 마우스 커서 위치 가져오기
        cursor_pos = event.position()

        # 뷰포트에서의 마우스 위치
        scene_pos = self.graphics_view.mapToScene(cursor_pos.toPoint())

        # 새 줌 레벨 적용
        self.graphics_view.scale(self.zoom_factor, self.zoom_factor)

        # 줌 중심점 조정
        new_scene_pos = self.graphics_view.mapToScene(cursor_pos.toPoint())
        delta = new_scene_pos - scene_pos
        self.graphics_view.translate(delta.x(), delta.y())

        # 이벤트 수용
        event.accept()

    def closeEvent(self, event):
        if self.video_capture:
            self.video_capture.release()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec())