import os
import glob
import pandas as pd

def main():

    # 指定文件夹路径
    folder_path = os.path.join(os.getenv('DATA_DIR'), 'csv')

    # 查找文件夹中所有以 _merged_results.csv 结尾的文件
    file_paths = glob.glob(os.path.join(folder_path, '*_merged_results.csv'))

    # 遍历每个文件并进行处理
    for file_path in file_paths:
        print(f"正在处理文件: {file_path}")
        
        # 读取CSV文件
        data = pd.read_csv(file_path)

        # 将time列转换为日期格式，并格式化为字符串以保留秒数
        data['time'] = pd.to_datetime(data['time'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')

        # 定义新的列名映射，包括time改为時間
        columns_mapping = {
            'time': '時間',
            'Mart': '連鎖商店',
            'car': '汽車',
            'motorcycle': '機車',
            'person': '人',
            'license-plate': '車牌號碼',
            'doorplate': '門牌',
            'street-signs': '路牌'
        }

        # 将原始列名替换为新的列名
        data.rename(columns=columns_mapping, inplace=True)

        # 定义需要处理的栏位
        columns_to_check = ['連鎖商店', '汽車', '機車', '人', '車牌號碼', '門牌', '路牌']

        # 初始化一个包含时间的DataFrame，用于合并
        combined_data = pd.DataFrame(data['時間'])

        # 为每个列生成过滤后的数据，并合并到 combined_data 中
        for column in columns_to_check:
            # 检查列的数据类型并过滤 '0' 和空字符串
            if column in data.columns:
                if data[column].dtype == 'object':
                    # 如果是字符串类型，排除 '0' 和空字符串
                    filtered_data = data[(data[column].str.strip() != '') & (data[column] != '0')][['時間', column]]
                else:
                    # 如果是数字类型，过滤非0的数值
                    filtered_data = data[data[column] != 0][['時間', column]]

                # 检查是否该列全为空或全为0
                if not filtered_data.empty:
                    # 如果列不全为空或不全为0，合并该列
                    combined_data = pd.merge(combined_data, filtered_data, on='時間', how='outer') 

        # 获取 combined_data 中现有的列，避免 KeyError
        existing_columns_to_check = [col for col in columns_to_check if col in combined_data.columns]

        # 检查是否所有列（除了'時間'）都是空值，若是则删除该行
        if existing_columns_to_check:
            combined_data.dropna(how='all', subset=existing_columns_to_check, inplace=True)

        # 构建输出文件路径，保存处理后的数据为Excel
        excel_path = os.path.join(os.getenv('DATA_DIR'), '..', 'excel')
        if not os.path.exists(excel_path):
            os.mkdir(excel_path)
        output_path = os.path.join(excel_path, os.path.basename(file_path).replace('_merged_results.csv', '_預設類別清單.xlsx'))

        # 使用ExcelWriter保存文件并指定时间格式
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            combined_data.to_excel(writer, index=False, sheet_name='ProcessedData')

            # 获取工作表对象
            workbook  = writer.book
            worksheet = writer.sheets['ProcessedData']

            # 定义日期时间格式
            time_format = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss'})

            # 去掉标题行粗体样式
            for col_num, value in enumerate(combined_data.columns.values):
                worksheet.write(0, col_num, value, workbook.add_format({'bold': False}))  # 禁用粗体

            # 设置 '時間' 列的格式
            worksheet.set_column('A:A', 20, time_format)
        print(f"文件处理完成并保存为: {output_path}")
