import pandas as pd
import os

def convert_to_yes_no(df):
    # 保留的指定列
    columns_to_convert = ['mart', 'car', 'motorcycle', 'person', 'license-plate', 'doorplate', 'street-signs']
    
    # 对其他数值型列进行转换
    for col in df.columns:
        if col not in columns_to_convert and pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].apply(lambda x: 'no' if x == 0 else ('yes' if x > 0 else x))
    
    return df

def replace_none_with_zero(df):
    # 將所有包含 'none' 的值替換為 '0'
    return df.applymap(lambda x: '0' if 'none' in str(x) else x)

def format_time(time_str):
    date_part, time_part = time_str.split(' ')
    formatted_time = time_part.replace('-', ':')
    return f"{date_part} {formatted_time}"

def merge_csv(video_id, base_dir, output_dir):
    
    dino_path = os.path.join(base_dir, f"{video_id}_DINO_results.csv")
    mart_path = os.path.join(base_dir, f"{video_id}_results.csv")

    # 讀取 CSV 文件
    dino_df = pd.read_csv(dino_path)
    mart_df = pd.read_csv(mart_path)

    # 將所有包含 'none' 的值替換為 '0'
    dino_df = replace_none_with_zero(dino_df)
    mart_df = replace_none_with_zero(mart_df)

    # 合併數據
    merged_df = pd.merge(mart_df, dino_df, on='time', how='outer')

    merged_df['time'] = merged_df['time'].apply(format_time)

    # 填充缺失值
    merged_df = merged_df.fillna('0')

    # 转换其他列为 'yes' 和 'no'
    merged_df = convert_to_yes_no(merged_df)

    # 保存合併後的數據到新的 CSV 文件
    output_path = os.path.join(output_dir, f"{video_id}_merged_results.csv")
    merged_df.to_csv(output_path, index=False)
    print(f"合併完成，結果已保存到 {output_path}")

def process_all_videos(datatime_path, base_dir, output_dir):
    # 讀取 datatime.csv 文件
    datatime_df = pd.read_csv(datatime_path)

    # 迭代所有影片名稱
    for video_name in datatime_df['影片名稱']:
        # 去除文件的 .mp4 扩展名
        video_id = os.path.splitext(video_name)[0]
        merge_csv(video_id, base_dir, output_dir)

def main():
    # 路徑設置
    datetime_path = os.path.join(os.getenv('DATA_DIR'), 'datetime.csv')
    base_dir = os.path.join(os.getenv('DATA_DIR'), 'csv')
    output_dir = os.path.join(os.getenv('DATA_DIR'), 'csv')

    # 執行合併
    process_all_videos(datetime_path, base_dir, output_dir)