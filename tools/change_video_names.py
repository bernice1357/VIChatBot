import os
import pandas as pd

def main(file_paths, df):
    # 確保列表和dataframe的長度一致
    if len(df) != len(file_paths):
        raise ValueError("Dataframe的行數和文件路徑列表的長度不一致")

    new_file_paths = []

    for index, row in df.iterrows():
        # 提取日期和時間
        date = row['影片發生日期']
        time = row['影片起始時間']
        
        # 格式化新文件名
        new_filename = f"{date.replace('-', '')}_{time.replace(':', '')}.mp4"
        
        # 獲取當前文件的完整路徑
        old_filepath = file_paths[index]
        
        # 獲取文件所在目錄
        dir_name = os.path.dirname(old_filepath)
        
        # 拼接新的文件路徑
        new_filepath = os.path.join(dir_name, new_filename)
        
        # 重命名文件
        os.rename(old_filepath, new_filepath)
        
        # 更新文件路径列表
        new_file_paths.append(new_filepath)
        
        # 更新DataFrame中的文件名
        df.at[index, '影片名稱'] = new_filename

    return new_file_paths, df
