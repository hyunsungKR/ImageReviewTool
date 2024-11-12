import sys
import cv2
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PySide6.QtGui import QImage, QPixmap, QTransform, QPainter, QWheelEvent
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF


class ZoomableGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setResizeAnchor(QGraphicsView.NoAnchor)
        self.zoom_factor = 1.0
        self.zoom_step = 0.1

    def wheelEvent(self, event: QWheelEvent):
        # 마우스 휠 이벤트 처리
        zoom_in = event.angleDelta().y() > 0

        # 이전 줌 팩터 저장
        old_zoom = self.zoom_factor

        # 줌 팩터 계산
        if zoom_in:
            self.zoom_factor *= (1 + self.zoom_step)
        else:
            self.zoom_factor /= (1 + self.zoom_step)

        # 줌 레벨 제한 (예: 0.1 ~ 10)
        self.zoom_factor = max(0.1, min(self.zoom_factor, 10))

        # 마우스 커서의 뷰포트 및 씬 좌표 얻기
        viewport_mouse_pos = event.position().toPoint()
        scene_mouse_pos = self.mapToScene(viewport_mouse_pos)

        # 새 줌 레벨 적용
        self.setTransform(QTransform().scale(self.zoom_factor, self.zoom_factor))

        # 줌 후 마우스 커서의 새로운 씬 좌표 계산
        new_scene_mouse_pos = self.mapToScene(viewport_mouse_pos)

        # 뷰포트 이동하여 마우스 커서 위치 유지
        delta = new_scene_mouse_pos - scene_mouse_pos
        self.translate(delta.x(), delta.y())

        # 이벤트 수용
        event.accept()


class VideoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Player with Zoom")
        self.setGeometry(100, 100, 800, 600)

        # 그래픽스 뷰 및 씬 설정
        self.graphics_view = ZoomableGraphicsView(self)
        self.setCentralWidget(self.graphics_view)
        self.scene = QGraphicsScene(self)
        self.graphics_view.setScene(self.scene)

        # 비디오 관련 변수 초기화
        self.video_capture = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.pixmap_item = None

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

            if self.pixmap_item is None:
                self.pixmap_item = self.scene.addPixmap(pixmap)
            else:
                self.pixmap_item.setPixmap(pixmap)

            # 씬 크기 설정
            self.scene.setSceneRect(0, 0, w, h)

            # 첫 프레임에서 뷰를 씬에 맞게 조정
            if self.graphics_view.zoom_factor == 1.0:
                self.graphics_view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        else:
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def closeEvent(self, event):
        if self.video_capture:
            self.video_capture.release()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec())