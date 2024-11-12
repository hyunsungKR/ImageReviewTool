import sys
from PySide6.QtWidgets import QApplication
from controller import ImageViewerController

'''
Model (ImageViewerModel): 
    데이터와 비즈니스 로직을 담당합니다. 
    파일 시스템 조작, 이미지 및 레이블 파일 관리 등을 처리합니다.
View (ImageViewerView): 
    사용자 인터페이스를 담당합니다. 이미지 표시, 트리 뷰, 확대/축소 등의 UI 요소를 관리합니다.
Controller (ImageViewerController): 
    Model과 View 사이의 중재자 역할을 합니다. 
    사용자 입력을 처리하고 Model의 데이터를 View에 반영합니다.
'''

if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = ImageViewerController()
    controller.view.show()
    sys.exit(app.exec())