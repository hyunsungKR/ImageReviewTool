import os
import cv2

def make_point_images(image_folder):
    # 대상 폴더 이름 추출
    folder_name = os.path.basename(image_folder.rstrip(os.sep))

    # 소스 이미지 폴더와 같은 경로에 대상 폴더 이름이 포함된 pointImages 폴더 생성
    point_images_base_folder = os.path.join(os.path.dirname(image_folder), f'{folder_name}_pointImages')
    if not os.path.exists(point_images_base_folder):
        os.makedirs(point_images_base_folder)

    for root, _, files in os.walk(image_folder):
        for filename in files:
            if filename.endswith('.jpg') or filename.endswith('.png'):
                image_path = os.path.join(root, filename)
                label_path = os.path.join(root, os.path.splitext(filename)[0] + '.txt')

                if os.path.exists(label_path):
                    image = cv2.imread(image_path)
                    if image is None:
                        print(f"Error reading image {image_path}")
                        continue

                    height, width, _ = image.shape

                    with open(label_path, 'r') as file:
                        for line in file:
                            try:
                                parts = line.strip().split()
                                class_id = int(parts[0])
                                if class_id != 3:  # 원하는 클래스 필터링
                                    continue
                                x_center, y_center, w, h = map(float, parts[1:])
                            except ValueError:
                                print(f"Error parsing line in {label_path}: {line.strip()}")
                                continue

                            # Bounding box 좌표 변환
                            x_center *= width
                            y_center *= height
                            w *= width
                            h *= height

                            x1 = int(x_center - w / 2)
                            y1 = int(y_center - h / 2)
                            x2 = int(x_center + w / 2)
                            y2 = int(y_center + h / 2)

                            # 유효한 좌표인지 확인
                            if x1 < 0 or y1 < 0 or x2 > width or y2 > height:
                                print(f"Invalid crop coordinates for {filename}: {x1}, {y1}, {x2}, {y2}")
                                continue

                            cropped_image = image[y1:y2, x1:x2]

                            if cropped_image.size == 0:
                                print(f"Cropped image is empty for {filename}")
                                continue

                            # 하위 폴더 구조를 유지하도록 생성할 폴더 경로 계산
                            relative_path = os.path.relpath(root, image_folder)
                            point_images_folder = os.path.join(point_images_base_folder, relative_path)

                            if not os.path.exists(point_images_folder):
                                os.makedirs(point_images_folder)

                            # 특수 문자를 제거하여 안전한 파일명 생성
                            safe_line = line.strip().replace(" ", "_").replace(":", "_")
                            cropped_image_name = f'pointImage_{os.path.splitext(filename)[0]}_{safe_line}.jpg'
                            cropped_image_path = os.path.join(point_images_folder, cropped_image_name)

                            # 이미지 저장
                            cv2.imwrite(cropped_image_path, cropped_image)
                            print(f"Saved {cropped_image_path}")

image_folder = r'D:\test\240926_TestDataset_Dent1000_Uneven1000'
make_point_images(image_folder)
