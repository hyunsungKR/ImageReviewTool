# ImageReviewTool 🖼️

* Ai Object Detection 모델 개발을 위한 데이터 이미지 검수 / 이미지 합성 툴

<div align="center"> <img src="https://img.shields.io/badge/PySide6-3776AB?style=flat-square&logo=Python&logoColor=white"/> <img src="https://img.shields.io/badge/NumPy-013243?style=flat-square&logo=NumPy&logoColor=white"/> <img src="https://img.shields.io/badge/OpenCV-5C3EE8?style=flat-square&logo=OpenCV&logoColor=white"/> </div>

## 📌 주요 기능

* 조명 방향 고려 스탬프 기능
이미지를 검수하며, 스탬프를 찍을 때 조명 방향을 자동으로 계산하여 적용할 수 있어 자연스러운 라벨링이 가능합니다.

* 확대 뷰로 세부 검수 편리성
검수를 돕기 위해 250%, 500%로 확대된 이미지와 전체 이미지를 한 화면에서 동시에 볼 수 있습니다.

* 핫키를 통한 빠른 이미지 필터링
키 하나로 이미지 검수에 불필요한 이미지를 빠르게 필터링하고 저장할 수 있어 생산성이 증가합니다.

## 📌 설치 방법

* 필요한 의존성 설치: pip install -r requirements.txt
* 실행 방법: python main.py
## 📌 프로젝트 구조
이 프로젝트는 MVC 패턴에 따라 코드가 구조화되어 있으며, 역할별로 분리되어 있어 유지 보수와 확장이 용이합니다.

* Model (model.py):
데이터와 비즈니스 로직을 관리하는 부분으로, 파일 시스템 조작, 이미지 파일 및 레이블 파일 관리를 처리합니다. 특히 이미지의 이동, 저장 폴더 생성 등의 로직이 포함되어 있어 데이터 관련 작업의 핵심을 담당합니다.

* View (view.py):
사용자 인터페이스를 관리하는 부분으로, 이미지와 확대 뷰, 라벨 오버레이 기능을 통해 사용자가 직관적으로 검수할 수 있도록 설계되어 있습니다. 사용자에게 제공되는 UI 요소와 확대 기능, 스탬프 기능, 필터링 작업을 모두 뷰에서 관리합니다.

* Controller (controller.py):
뷰와 모델 사이의 중재 역할을 수행하며, 뷰에서 발생한 이벤트(예: 이미지 선택, 스탬프 추가)를 모델에 전달하고 결과를 다시 뷰에 반영합니다. 이를 통해 MVC 패턴의 원칙을 지키면서, 사용자의 액션을 적절히 처리하고 각 컴포넌트 간의 의존성을 최소화합니다.
## 📌 예시 화면
전체 이미지와 확대 뷰
<img width="100%" src="https://example.com/full_image_view.jpg">

조명 방향 고려 스탬프 기능 예시
<img width="100%" src="https://example.com/stamp_with_light_direction.jpg">

