import os
import shutil
import re
import logging


# # 로깅 설정 # 필요시 주석 해제
# logging.basicConfig(
#     filename='file_organizer.log',
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     encoding='utf-8'  # 로그 파일 인코딩을 UTF-8로 설정
# )

# 원본 폴더와 대상 폴더 경로를 설정합니다.
# 모든 파일이 새로운 이름의 경로에 복사됩니다. 원본 파일은 그대로 유지됩니다.
source_dir = r'D:\test\khy\particle'
dest_dir = r'D:\test\khy\particle_sorted'

# 대상 폴더가 존재하지 않으면 생성합니다.
if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)
    logging.info(f"Created destination directory: {dest_dir}")

# 파일명을 분석하기 위한 정규 표현식을 정의합니다.
cam_regex = re.compile(r'(\d+cam)', re.IGNORECASE)  # Cam 번호 추출 (예: '2cam')
date_regex = re.compile(r'(\d{8})')  # 날짜 형식 추출 (예: '20240411')
pattern_regex = re.compile(r'_([yjYJ]\d{1,2})_')  # 패턴 추출 (_y0_, _j1_, _y10_, _j10_)

# 기타 제거할 패턴 정의
timestamp_regex = re.compile(r'\.\d+$')  # 소수점 숫자 (예: .445563)
pointimage_regex = re.compile(r'pointImage_', re.IGNORECASE)  # 'pointImage_' 제거
parentheses_regex = re.compile(r'\(.*?\)')  # 괄호 안의 내용 제거

# 이미지 파일 확장자 리스트
image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')


def extract_info(filename):
    """
    파일명에서 Cam 번호, 날짜, 패턴을 추출하는 함수.
    """
    try:
        # 'pointImage_' 제거
        base_name = pointimage_regex.sub('', filename)

        # 괄호 안의 내용 제거
        base_name = parentheses_regex.sub('', base_name)

        # 소수점 숫자 제거
        base_name = timestamp_regex.sub('', base_name)

        # Cam 번호 추출
        cam_match = cam_regex.search(base_name)
        cam = cam_match.group(1) if cam_match else None

        # 날짜 추출
        date_match = date_regex.search(base_name)
        date = date_match.group(1) if date_match else None

        # 패턴 추출
        pattern_match = pattern_regex.search(base_name)
        pattern = pattern_match.group(1) if pattern_match else 'no_pattern'

        return cam, date, pattern
    except Exception as e:
        logging.error(f"Error extracting info from filename '{filename}': {e}")
        return None, None, 'error_pattern'


def copy_file(src, dst):
    """
    파일을 복사합니다. 이미 존재하는 경우 덮어쓰지 않습니다.
    """
    try:
        if not os.path.exists(dst):
            shutil.copy2(src, dst)
            logging.info(f"Copied '{src}' to '{dst}'")
        else:
            logging.info(f"Skipped copying '{src}' as it already exists in '{dst}'")
    except Exception as e:
        logging.error(f"Error copying file '{src}' to '{dst}': {e}")


# os.walk를 사용하여 모든 하위 디렉토리를 순회합니다.
for root, _, files in os.walk(source_dir):
    for filename in files:
        # 이미지 파일만 처리합니다.
        if filename.lower().endswith(image_extensions):
            try:
                # 패턴 추출
                cam, date, pattern = extract_info(filename)

                # 캠 번호와 날짜에 따라 폴더명 설정
                if cam and date:  # 캠과 날짜가 모두 있을 경우
                    folder_name = f"{cam}_{date}"
                elif date:  # 날짜만 있을 경우
                    folder_name = f"{date}"
                elif cam:  # 캠 정보만 있을 경우
                    folder_name = f"{cam}"
                else:  # 캠 번호와 날짜가 없을 경우
                    folder_name = 'unknown'

                # 대상 폴더 내에 패턴 이름의 폴더를 생성합니다.
                folder_path = os.path.join(dest_dir, folder_name)
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                    logging.info(f"Created folder: {folder_path}")

                # 원본 파일의 전체 경로
                src_file = os.path.join(root, filename)
                # 대상 파일의 전체 경로
                dst_file = os.path.join(folder_path, filename)

                # 이미지 파일을 대상 폴더로 복사합니다.
                copy_file(src_file, dst_file)

                # 동일한 이름의 텍스트 파일이 있으면 함께 복사합니다.
                base_name_no_ext = os.path.splitext(filename)[0]
                text_file_name = base_name_no_ext + '.txt'
                text_file_path = os.path.join(root, text_file_name)
                dst_text_file = os.path.join(folder_path, text_file_name)
                if os.path.exists(text_file_path):
                    copy_file(text_file_path, dst_text_file)
            except Exception as e:
                logging.error(f"Error processing file '{filename}' in '{root}': {e}")

print("파일 정리가 완료되었습니다.")
logging.info("파일 정리가 완료되었습니다.")
