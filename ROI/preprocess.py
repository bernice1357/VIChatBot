import pandas as pd
import cv2
import numpy as np
import os

def preprocess_videos(video_dir, datetime_path, reid_path, output_path, mode):
    
    # 讀取 datetime.csv 文件，並正確處理列名
    datetime_df = pd.read_csv(datetime_path, delimiter=',')
    
    # 清理列名中的空白字符
    datetime_df.columns = datetime_df.columns.str.strip()
    
    # 讀取 test.txt 文件
    test_df = pd.read_csv(reid_path, delimiter=' ', header=None)

    # 解析 test.txt 中的 video id
    video_ids = test_df[0].unique()

    # 定義一個函數來獲取視頻信息
    def get_video_info(video_path):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        
        cap.release()
        return fps, frame_count, duration

    # 創建一個列表來存儲所有的結果
    results = []

    if mode=='single':

        # 找到對應的影片信息
        video_info = datetime_df[datetime_df['ID'] == 1].iloc[0]
        video_name = video_info['影片名稱']
        video_path = os.path.join(video_dir, video_name)

        # 獲取視頻信息
        fps, frame_count, duration = get_video_info(video_path)
        frame_dict = {}

        for video_id in video_ids:
            
            # 根據 video_id 過濾出 test.txt 中的對應行
            video_test_df = test_df[test_df[0] == video_id]

            # 創建一個 dict 來存儲幀數信息，使用 frame_num 作为键
            
            # 將 test.txt 中的幀數信息填入 dict
            for _, row in video_test_df.iterrows():

                if video_id==1:
                    frame_num = row[2] - 1  # 調整索引從 0 開始
                else:
                    frame_num = row[2] - 1 + frame_count//2 # 調整索引從 0 開始

                if frame_num < frame_count:  # 檢查 frame_num 是否在範圍內
                    if frame_num not in frame_dict:
                        frame_dict[frame_num] = []
                    frame_dict[frame_num].append([1, row[1], frame_num, row[3], row[4], row[5], row[6]])
                    # print([1, row[1], row[2], row[3], row[4], row[5], row[6]])

        # 獲取已存在的幀數
        existing_frames = sorted(frame_dict.keys())
        # print('frame_dict',existing_frames)

        # 找到最小和最大幀
        # 找到最小和最大幀
        min_frame = 0  # 确保从第 1 帧开始填充
        max_frame = int(fps * duration) - 1
        
        # 遍历范围内的所有帧并填充缺失的帧
        for i in range(min_frame, max_frame + 1):
            if i not in frame_dict:
                frame_dict[i] = [[1, 0, i + 1, 0, 0, 0, 0]]

        for key in sorted(frame_dict.keys()):
            for entry in frame_dict[key]:
                results.append(entry)

        for i in results:
            print(i)
            
    else:      
        
        for video_id in video_ids:
            # 找到對應的影片信息
            video_info = datetime_df[datetime_df['ID'] == video_id].iloc[0]
            video_name = video_info['影片名稱']
            video_path = os.path.join(video_dir, video_name)
            
            # 獲取視頻信息
            fps, frame_count, duration = get_video_info(video_path)
            
            # 根據 video_id 過濾出 test.txt 中的對應行
            video_test_df = test_df[test_df[0] == video_id]

            # 創建一個 dict 來存儲幀數信息，使用 frame_num 作为键
            frame_dict = {}

            # 將 test.txt 中的幀數信息填入 dict
            for _, row in video_test_df.iterrows():
                frame_num = row[2] - 1  # 調整索引從 0 開始
                if frame_num < frame_count:  # 檢查 frame_num 是否在範圍內
                    if frame_num not in frame_dict:
                        frame_dict[frame_num] = []
                    frame_dict[frame_num].append([video_id, row[1], row[2], row[3], row[4], row[5], row[6]])

            # 獲取已存在的幀數
            existing_frames = sorted(frame_dict.keys())

            # 找到最小和最大幀
            # 找到最小和最大幀
            min_frame = 0  # 确保从第 1 帧开始填充
            max_frame = int(fps * duration) - 1
            
            # 遍历范围内的所有帧并填充缺失的帧
            for i in range(min_frame, max_frame + 1):
                if i not in frame_dict:
                    frame_dict[i] = [[video_id, 0, i + 1, 0, 0, 0, 0]]

            for key in sorted(frame_dict.keys()):
                for entry in frame_dict[key]:
                    results.append(entry)

    # 將結果保存為 CSV 文件
    results_df = pd.DataFrame(results, columns=['video_id', 'id', 'frame', 'x', 'y', 'w', 'h'])
    results_df.to_csv(output_path, index=False)

def main(mode='normal'):
    video_dir = os.path.join(os.getenv('DATA_DIR'), 'input_videos')
    datetime_path = os.path.join(os.getenv('DATA_DIR'), 'datetime.csv')
    reid_path = os.path.join(os.getenv('DATA_DIR'), 'reid', 'reid_output.txt')
    output_path = os.path.join(os.getenv('DATA_DIR'), 'roi_output.csv')
    preprocess_videos(video_dir, datetime_path, reid_path, output_path, mode)