import os
from moviepy.video.io.VideoFileClip import VideoFileClip

def split_video(video_path, output_dir=None):
    # 讀取影片
    clip = VideoFileClip(video_path)

    # 取得影片長度的一半時間
    duration = clip.duration
    half_duration = duration/2

    # 取得檔案名稱和副檔名
    filename = os.path.basename(video_path)
    file_extension = os.path.splitext(video_path)[1]
    filename_without_ext = os.path.splitext(filename)[0]
    # 如果有指定輸出路徑，則使用；否則使用影片所在的目錄
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)  # 建立輸出目錄（若不存在）
    else:
        output_dir = os.path.dirname(video_path)
    # 定義輸出檔案路徑
    output1 = os.path.join(output_dir, f'{filename_without_ext}_part1{file_extension}')
    output2 = os.path.join(output_dir, f'{filename_without_ext}_part2{file_extension}')
    
    # 分割影片為兩個部分
    clip1 = clip.subclip(0, half_duration)
    clip2 = clip.subclip(half_duration, duration)
    
    # 寫入分割後的影片
    clip1.write_videofile(output1, codec="libx264", audio_codec="aac")
    clip2.write_videofile(output2, codec="libx264", audio_codec="aac")
    
    print(f"影片已分割為兩部：{output1}, {output2}")

def main(video_path):
    output_dir = os.path.join(os.getenv('DATA_DIR'), 'single_reid')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    split_video(video_path, output_dir)