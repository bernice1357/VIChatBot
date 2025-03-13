import os
import subprocess
from pathlib import Path
import imageio_ffmpeg as ffmpeg
from datetime import datetime, timedelta
import pandas as pd

def extract_frames_ffmpeg(video_path, output_dir, fps=1):
    os.makedirs(output_dir, exist_ok=True)
    video_name = Path(video_path).name  # 使用完整文件名
    # print(video_name)
    # video_name = video_name[:-4]
    frame_output_pattern = os.path.join(output_dir, f"{video_name}_%08d.jpg")
    ffmpeg_path = ffmpeg.get_ffmpeg_exe()
    ffmpeg_command = [
        ffmpeg_path,
        "-i", str(video_path),
        "-vf", f"fps={fps}",
        frame_output_pattern
    ]
    subprocess.run(ffmpeg_command)
    print(f"Frames extracted to {output_dir} for video {video_name}")

def rename_frames(output_dir, start_time, fps=1):
    frames = sorted(Path(output_dir).glob('*.jpg'))
    time_format = "%Y-%m-%d %H:%M:%S"
    start_datetime = datetime.strptime(start_time, time_format)
    
    for i, frame in enumerate(frames):
        current_time = start_datetime + timedelta(seconds=i // fps, microseconds=(i % fps) * (1000000 // fps))
        new_name = current_time.strftime("%Y-%m-%d %H-%M-%S.jpg")
        frame.rename(Path(output_dir) / new_name)
    print(f"Frames renamed in {output_dir}")

def extract_start_time_from_csv(video_name, csv_path):
    df = pd.read_csv(csv_path)
    video_info = df[df['影片名稱'] == video_name].iloc[0]
    start_time = f"{video_info['影片發生日期']} {video_info['影片起始時間']}"
    return start_time

def extract_frames_from_directory_ffmpeg(video_dir, output_dir, csv_path, fps=1):
    os.makedirs(output_dir, exist_ok=True)
    video_files = list(Path(video_dir).glob('*.mp4'))

    for video_file in video_files:
        video_output_dir = os.path.join(output_dir, video_file.stem)
        extract_frames_ffmpeg(video_file, video_output_dir, fps)
        
        video_name = video_file.name  # 使用完整文件名
        start_time = extract_start_time_from_csv(video_name, csv_path)
        rename_frames(video_output_dir, start_time, fps)

def main():

    input_path = os.path.join(os.getenv('DATA_DIR'), 'input_videos')
    output_path = os.path.join(os.getenv('DATA_DIR'), 'video_frames')
    datetime_path = os.path.join(os.getenv('DATA_DIR'), 'datetime.csv')

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    extract_frames_from_directory_ffmpeg(input_path, output_path, datetime_path)