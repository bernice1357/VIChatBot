import pandas as pd
import os

def main(input_paths, data):
    # 处理DataFrame
    df = pd.DataFrame(data)

    # 创建ID栏位，直接按照DataFrame的顺序分配ID
    df['ID'] = range(1, len(df) + 1)

    # 重新排列栏位顺序
    df = df[['ID', '影片名稱', '影片發生日期', '影片起始時間']]

    # 将DataFrame保存为CSV文件
    csv_path = os.getenv('DATA_DIR')+'/datetime.csv'
    df.to_csv(csv_path, index=False, encoding='utf-8')
