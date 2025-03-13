import cv2
import pandas as pd
import os
from datetime import datetime, timedelta

def get_fps(video_path):
    """获取视频的FPS（每秒帧数）"""
    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        raise FileNotFoundError(f"视频文件未找到: {video_path}")
    fps = video.get(cv2.CAP_PROP_FPS)
    video.release()
    if fps == 0:
        raise ValueError(f"无法从视频获取有效的FPS: {video_path}")
    return fps

def detect_box(image_path, csv_path):
    """检测ROI区域，并判断目标对象是否在该区域内"""
    image = cv2.imread(image_path)
    if image is None:
        print(f"无法读取图像文件: {image_path}")
        return None
    
    # 转为灰度图并进行边缘检测
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray_image, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        print("未检测到目标框")
        return None

    # 获取最大的轮廓并定义为ROI区域
    x, y, w, h = cv2.boundingRect(max(contours, key=cv2.contourArea))
    roi = image[y:y+h, x:x+w]
    hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # 检测ROI区域的颜色（红色或蓝色）
    mask1 = cv2.inRange(hsv_roi, (0, 50, 50), (10, 255, 255))
    mask2 = cv2.inRange(hsv_roi, (170, 50, 50), (180, 255, 255))
    red_pixels = cv2.countNonZero(mask1 | mask2)
    color = 'r' if red_pixels > 0 else 'b'

    # 读取跟踪数据
    data = pd.read_csv(csv_path)
    tracking_data = []

    # 判断目标对象是否在ROI区域内
    for _, row in data.iterrows():
        center_x = row['x'] + row['w'] // 2
        center_y = row['y'] + row['h'] // 2
        
        # 如果id为0，设为None
        row_id = None if row['id'] == 0 else row['id']
        
        # 如果id为None，则in也设为None
        if row_id is None:
            in_box = None
        else:
            in_box = 1 if (x <= center_x <= x + w) and (y <= center_y <= y + h) else 0
        
        tracking_data.append([row['video_id'], row['frame'], row_id, in_box, color])
    # 返回处理后的跟踪数据
        df = pd.DataFrame(tracking_data, columns=['video_id', 'frame', 'id', 'in', 'color'])

    # 输出为CSV文件
        output_csv_path = os.path.join(os.getenv('DATA_DIR'), 'csv', 'fanming.csv')
        df.to_csv(output_csv_path, index=False)
    return pd.DataFrame(tracking_data, columns=['video_id', 'frame', 'id', 'in', 'color'])

def merge_tracking_data(datatime_path, tracking_data, threshold=5):
    """合并跟踪数据与时间戳，并计算STAY，区分红框和蓝框"""
    datatime_df = pd.read_csv(datatime_path, encoding='utf-8')
    video_dir = os.path.dirname(datatime_path)
    all_final_data = []
    
    for video_id in tracking_data['video_id'].unique():
        datatime_row = datatime_df[datatime_df['ID'] == video_id]
        if datatime_row.empty:
            continue
        
        video_name = os.path.join(video_dir, 'input_videos', f"{datatime_row.iloc[0]['影片名稱']}")
        try:
            fps = get_fps(video_name)
        except ValueError as e:
            print(e)
            continue  # 跳过无法打开的视频
        
        start_datetime_str = f"{datatime_row.iloc[0]['影片發生日期']} {datatime_row.iloc[0]['影片起始時間']}"
        start_datetime = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M:%S")
        
        video_tracking_df = tracking_data[tracking_data['video_id'] == video_id].sort_values('frame').reset_index(drop=True)
        total_frames = int(video_tracking_df['frame'].max())
        total_seconds = int(total_frames // fps) + 1
        
        final_data_df = pd.DataFrame({
            'time': [(start_datetime + timedelta(seconds=i)).strftime("%Y-%m-%d %H:%M:%S") for i in range(total_seconds)],
            'in': 0,
            'out': 0,
            'stay': 0
        })
        
        for obj_id, group in video_tracking_df.groupby('id'):
            if pd.isna(obj_id):
                continue
            group = group.sort_values('frame').reset_index(drop=True)
            first_5_frames = group.iloc[:5]
            last_5_frames = group.iloc[-5:]
            color = group['color'].iloc[0]  # 取该对象的颜色
            
            if color == 'r':
                # 红框：正常判定逻辑
                if first_5_frames['in'].sum() == 0 and last_5_frames['in'].sum() > 0:
                    last_in_frame = last_5_frames[last_5_frames['in'] == 1].iloc[-1]
                    in_second = int(last_in_frame['frame'] // fps)
                    if in_second < total_seconds:
                        final_data_df.at[in_second, 'in'] += 1
                
                elif first_5_frames['in'].sum() > 0 and last_5_frames['in'].sum() == 0:
                    first_in_frame = first_5_frames[first_5_frames['in'] == 1].iloc[0]
                    out_second = int(first_in_frame['frame'] // fps)
                    if out_second < total_seconds:
                        final_data_df.at[out_second, 'out'] += 1
                
                elif first_5_frames['in'].sum() == 0 and last_5_frames['in'].sum() == 0:
                    in_period = group[(group['in'] == 1)]
                    if not in_period.empty:
                        first_in_time = in_period.iloc[0]['frame'] // fps
                        last_in_time = in_period.iloc[-1]['frame'] // fps
                        if last_in_time - first_in_time >= threshold:
                            final_data_df.at[int(first_in_time), 'in'] += 1
                            final_data_df.at[int(last_in_time), 'out'] += 1

            elif color == 'b':
                # 蓝框：反转判定逻辑
                if first_5_frames['in'].sum() == 0 and last_5_frames['in'].sum() > 0:
                    last_in_frame = last_5_frames[last_5_frames['in'] == 1].iloc[-1]
                    out_second = int(last_in_frame['frame'] // fps)
                    if out_second < total_seconds:
                        final_data_df.at[out_second, 'out'] += 1
                
                elif first_5_frames['in'].sum() > 0 and last_5_frames['in'].sum() == 0:
                    first_in_frame = first_5_frames[first_5_frames['in'] == 1].iloc[0]
                    in_second = int(first_in_frame['frame'] // fps)
                    if in_second < total_seconds:
                        final_data_df.at[in_second, 'in'] += 1
                
                elif first_5_frames['in'].sum() == 0 and last_5_frames['in'].sum() == 0:
                    in_period = group[(group['in'] == 1)]
                    if not in_period.empty:
                        first_in_time = in_period.iloc[0]['frame'] // fps
                        last_in_time = in_period.iloc[-1]['frame'] // fps
                        if last_in_time - first_in_time >= threshold:
                            final_data_df.at[int(last_in_time), 'out'] += 1
                            final_data_df.at[int(first_in_time), 'in'] += 1
        
        current_stay = 0
        consecutive_zeros = 0

        for idx, row in final_data_df.iterrows():
            second_frames = video_tracking_df[video_tracking_df['frame'] // fps == idx]
            in_count = second_frames['in'].sum()
            
            if in_count > 0:
                current_stay += 1
                consecutive_zeros = 0
            else:
                consecutive_zeros += 1
                if consecutive_zeros >= 1:
                    current_stay = 0
            
            final_data_df.at[idx, 'stay'] = current_stay
        
        all_final_data.append(final_data_df)
    
    if all_final_data:
        final_data_all_videos = pd.concat(all_final_data, ignore_index=True)
        final_data_all_videos = final_data_all_videos.sort_values('time').reset_index(drop=True)
        return final_data_all_videos
    else:
        return pd.DataFrame(columns=['time', 'in', 'out', 'stay'])


# 主程序
def main(threshold):
    image_path = os.path.join(os.getenv('DATA_DIR'), 'roi_box.png')
    csv_path = os.path.join(os.getenv('DATA_DIR'), 'roi_output.csv')
    datetime_path = os.path.join(os.getenv('DATA_DIR'), 'datetime.csv')

    if not os.path.exists(os.path.join(os.getenv('DATA_DIR'), 'csv')):
        os.makedirs(os.path.join(os.getenv('DATA_DIR'), 'csv'))

    tracking_data = detect_box(image_path, csv_path)
    if tracking_data is not None:
        merged_df = merge_tracking_data(datetime_path, tracking_data, threshold)
        output_path = os.path.join(os.getenv('DATA_DIR'), 'csv', 'in_out.csv')
        merged_df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"數據已保存 in_out.csv")
    else:
        print("未生成跟踪数据，程序结束。")