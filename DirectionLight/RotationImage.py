import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 한글 폰트 설정 (맑은 고딕 사용)
font_path = 'C:/Windows/Fonts/malgun.ttf'
font_prop = fm.FontProperties(fname=font_path)


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
    rotated = cv2.warpAffine(image, M, (w, h))

    return rotated


# 배경 이미지와 아이콘 이미지 로드 (경로를 수정하세요)
background_image = cv2.imread('background.jpg', cv2.IMREAD_GRAYSCALE)
icon_image = cv2.imread('icon.png', cv2.IMREAD_GRAYSCALE)

# 배경 이미지에서 주요 방향 검출
main_direction, magnitude, direction = get_main_direction(background_image)
main_direction_degrees = np.degrees(main_direction)

# 아이콘 이미지 회전
rotated_icon_image = rotate_image(icon_image, main_direction_degrees)

# 정보 출력
print(f"배경 이미지의 주요 방향 (라디안): {main_direction:.2f}")
print(f"배경 이미지의 주요 방향 (도): {main_direction_degrees:.2f}도")
print(f"아이콘 이미지의 크기: {icon_image.shape}")
print(f"회전된 아이콘 이미지의 크기: {rotated_icon_image.shape}")
print(f"빛의 방향으로 회전한 각도: {main_direction_degrees:.2f}도")

# 결과 시각화
plt.figure(figsize=(12, 6))

plt.subplot(2, 3, 1)
plt.title('배경 이미지', fontproperties=font_prop)
plt.imshow(background_image, cmap='gray')

plt.subplot(2, 3, 2)
plt.title('에지 검출 결과', fontproperties=font_prop)
plt.imshow(magnitude, cmap='gray')

plt.subplot(2, 3, 3)
plt.title('방향 히스토그램', fontproperties=font_prop)
plt.hist(direction.ravel(), bins=180, range=(-np.pi, np.pi))
plt.axvline(main_direction, color='r', linestyle='--')

plt.subplot(2, 3, 4)
plt.title('회전 전 아이콘 이미지', fontproperties=font_prop)
plt.imshow(icon_image, cmap='gray')

plt.subplot(2, 3, 5)
plt.title('회전 후 아이콘 이미지', fontproperties=font_prop)
plt.imshow(rotated_icon_image, cmap='gray')

plt.tight_layout()
plt.show()
