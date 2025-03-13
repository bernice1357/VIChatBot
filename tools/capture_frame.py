import os
import cv2
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

def extract_frame(video_path, output_dir):
    # 確保輸出目錄存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 打開影片檔案
    cap = cv2.VideoCapture(video_path)
    
    # 檢查影片是否打開成功
    if not cap.isOpened():
        print(f"Error opening video file: {video_path}")

    # 設置幀位置
    cap.set(cv2.CAP_PROP_POS_FRAMES, 9)
    
    # 讀取幀
    ret, frame = cap.read()
    if ret:
        # 生成輸出文件名
        frame_name = "image.jpg"
        output_path = os.path.join(output_dir, frame_name)
        
        # 保
        cv2.imwrite(output_path, frame)
        # print(f"Saved {output_path}")
    else:
        print(f"Failed to read frame from {video_path}")
    
    # 釋放影片檔案
    cap.release()

def get_output_path(full_path):
    output_path = ""
    while True:
        full_path, folder = os.path.split(full_path)
        if folder == "gradio":
            output_path = os.path.join(full_path, folder)
            break
        elif not folder:
            break

    return os.path.join(output_path, 'label_image')

def capture_frame(video_list):
    if not video_list:
        print("No video files provided.")
        return
    
    first_video = video_list[0]
    output_dir = get_output_path(first_video)
    extract_frame(first_video, output_dir)