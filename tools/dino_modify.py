import pandas as pd
import os

def process_dino_files(directory):

    def transform_value(value):
        try:
            # 转换为整数以进行比较
            int_value = int(value)
            if int_value > 0:
                return 'yes'
            else:
                return 'no'
        except ValueError:
            # 处理无法转换为整数的值
            return 'no'

    for filename in os.listdir(directory):
        if filename.endswith('_DINO_results.csv'):
            file_path = os.path.join(directory, filename)

            df = pd.read_csv(file_path)

            column_name = df.columns[1]  # 假设需要处理的列是第二列

            df[column_name] = df[column_name].apply(transform_value)

            df.to_csv(file_path, index=False)