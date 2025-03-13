import os
import shutil

def copy_videos(src_dir, dst_dir):
    # 确保目标目录存在，如果不存在则创建
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)

    # 定义常见的视频文件扩展名
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.mpeg')

    # 遍历源目录中的所有文件
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith(video_extensions):
                src_file = os.path.join(root, file)
                dst_file = os.path.join(dst_dir, file)
                # 复制视频文件到目标目录
                shutil.copy2(src_file, dst_file)