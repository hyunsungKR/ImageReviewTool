import cv2
import numpy as np
import ctypes


def get_main_direction(image):
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


def rotate_image(image, angle):
    # 이미지 중심 계산
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)

    # 회전 행렬 생성
    M = cv2.getRotationMatrix2D(center, angle, 1.0)

    # 이미지 회전
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                             borderValue=(0, 0, 0, 0))

    return rotated


def alpha_blend(background, foreground):
    # 배경과 전경 크기가 같은지 확인
    if background.shape[:2] != foreground.shape[:2]:
        raise ValueError("배경과 전경 이미지의 크기가 같아야 합니다.")

    # 알파 채널 분리
    b, g, r, a = cv2.split(foreground)
    alpha = a / 255.0
    alpha = cv2.merge([alpha, alpha, alpha])

    # 알파 블렌딩
    blended = cv2.convertScaleAbs(background * (1 - alpha) + foreground[:, :, :3] * alpha)
    return blended


def place_icon_on_background(background, icon, position):
    x, y = position
    h, w = icon.shape[:2]

    # 배경에서 아이콘 영역 추출
    background_region = background[y:y + h, x:x + w]

    # 배경 영역에서 주요 방향 검출
    main_direction, magnitude, direction = get_main_direction(background_region)
    main_direction_degrees = np.degrees(main_direction)

    # 아이콘 이미지 회전
    rotated_icon_image = rotate_image(icon, main_direction_degrees)

    # 회전된 아이콘을 배경에 합성
    result = background.copy()
    blended_region = alpha_blend(background_region, rotated_icon_image)
    result[y:y + h, x:x + w] = blended_region

    return result, main_direction_degrees


# 배경 이미지와 아이콘 이미지 로드 (경로를 수정하세요)
background_image = cv2.imread('background.jpg', cv2.IMREAD_COLOR)
icon_image = cv2.imread('icon.png', cv2.IMREAD_UNCHANGED)
icon_height, icon_width = icon_image.shape[:2]


# 마우스 콜백 함수
def mouse_move(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
        # 아이콘의 위치를 중앙에 맞추기 위해 좌표 조정
        icon_position = (x - icon_width // 2, y - icon_height // 2)

        # 아이콘을 배치할 위치가 이미지 경계를 벗어나지 않도록 조정
        icon_position = (max(0, min(icon_position[0], background_image.shape[1] - icon_width)),
                         max(0, min(icon_position[1], background_image.shape[0] - icon_height)))

        # 배경에 아이콘 배치
        result_image, rotation_angle = place_icon_on_background(background_image, icon_image, icon_position)

        # 결과 이미지 표시
        cv2.imshow('Result', result_image)




# 윈도우 설정 및 마우스 콜백 함수 등록
cv2.namedWindow('Result')
cv2.setMouseCallback('Result', mouse_move)

# 초기 이미지 표시
cv2.imshow('Result', background_image)
#cv2.waitKey(0)

# 키 이벤트 처리
cursor_visible = True
while True:
    key = cv2.waitKey(1) & 0xFF
    if key != 255:
        print(key)
    if key == ord('q'):
        break
    elif key == 17:  # Ctrl 키 코드
        if cursor_visible:
            # 커서 숨기기
            ctypes.windll.user32.ShowCursor(False)
            cursor_visible = False
    else:
        if not cursor_visible:
            # 커서 다시 보이기
            ctypes.windll.user32.ShowCursor(True)
            cursor_visible = True

    ctypes.windll.user32.ShowCursor(False)
cv2.destroyAllWindows()
