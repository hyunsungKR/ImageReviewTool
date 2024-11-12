import os
import cv2
import traceback

def make_point_images(base_folder):
    try:
        # 최상위 폴더 이름 추출
        top_folder_name = os.path.basename(base_folder.rstrip(os.sep))

        # 최상위 폴더와 같은 경로에 최상위 폴더 이름이 포함된 pointImages 폴더 생성
        point_images_base_folder = os.path.join(os.path.dirname(base_folder), f'{top_folder_name}_pointImages')

        # 저장할 폴더가 없으면 생성
        if not os.path.exists(point_images_base_folder):
            os.makedirs(point_images_base_folder)

        # os.walk로 하위 폴더들까지 모두 순회
        for root, _, files in os.walk(base_folder, topdown=True):
            # root 경로에서 base_folder와의 상대 경로 계산
            relative_path = os.path.relpath(root, base_folder)

            # 최상위 폴더가 아닌 경우에만 relative_path 적용
            if relative_path == ".":
                relative_path = ""

            # pointImages 폴더 내에 원본 폴더 구조를 유지하는 경로 생성
            point_images_folder = os.path.join(point_images_base_folder, relative_path)

            # 해당 경로가 존재하지 않으면 생성
            if not os.path.exists(point_images_folder):
                os.makedirs(point_images_folder)

            print(f"Processing folder: {root}, saving to: {point_images_folder}")  # 현재 처리 중인 경로 출력

            # 현재 폴더에 있는 파일들 처리
            for filename in files:
                print(f"Processing file: {filename}")
                if filename.lower().endswith(('.jpg', '.png')):
                    try:
                        image_path = os.path.join(root, filename)  # 이미지 파일 경로
                        label_filename = os.path.splitext(filename)[0] + '.txt'
                        label_path = os.path.join(root, label_filename)  # 레이블 파일 경로

                        if not os.path.exists(label_path):
                            print(f"Label file not found for image {filename}")
                            continue

                        image = cv2.imread(image_path)
                        if image is None:
                            print(f"Failed to read image {image_path}")
                            continue

                        height, width, _ = image.shape
                        with open(label_path, 'r', encoding='utf-8') as file:
                            for line in file:
                                try:
                                    parts = line.strip().split()
                                    if len(parts) < 5:
                                        print(f"Invalid label format in {label_path}: {line.strip()}")
                                        continue
                                    class_id = int(parts[0])
                                    if class_id not in desired_class_ids:  # 원하는 클래스만 필터링
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

                                x1 = int(x_center - w / 2 - label_margin)
                                y1 = int(y_center - h / 2 - label_margin)
                                x2 = int(x_center + w / 2 + label_margin)
                                y2 = int(y_center + h / 2 + label_margin)

                                # 좌표 출력
                                print(f"Crop coordinates for {filename}: x1={x1}, y1={y1}, x2={x2}, y2={y2}")

                                # 좌표가 이미지 범위를 벗어나지 않도록 조정
                                x1 = max(0, x1)
                                y1 = max(0, y1)
                                x2 = min(width, x2)
                                y2 = min(height, y2)

                                # 유효한 좌표인지 확인
                                if x1 >= x2 or y1 >= y2:
                                    print(f"Invalid crop coordinates for {filename}: {x1}, {y1}, {x2}, {y2}")
                                    continue

                                cropped_image = image[y1:y2, x1:x2]

                                if cropped_image.size == 0:
                                    print(f"Cropped image is empty for {filename}")
                                    continue

                                # 잘라낸 이미지의 저장 경로 설정
                                cropped_image_name = f'pointImage_{os.path.splitext(filename)[0]}.jpg'
                                cropped_image_path = os.path.join(point_images_folder, cropped_image_name)

                                # 저장 경로 출력
                                print(f"Saving cropped image to: {cropped_image_path}")

                                # 이미지 저장 및 성공 여부 확인
                                success = cv2.imwrite(cropped_image_path, cropped_image)
                                if not success:
                                    print(f"Failed to save image {cropped_image_path}")
                                else:
                                    print(f"Saved {cropped_image_path}")
                    except Exception as e:
                        print(f"Error processing file {filename}: {e}")
                        traceback.print_exc()
                        continue
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()

    print("Processing completed.")

# 설정 값
label_margin = 0
desired_class_ids = [2, 3]  # 원하는 클래스 인덱스 번호를 리스트로 설정합니다.
base_folder = r"D:\test\0922data_unevens"
make_point_images(base_folder)
