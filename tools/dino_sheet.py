import pandas as pd
import plotly.graph_objs as go
from dotenv import load_dotenv
import os
import shutil
from plotly.offline import plot
import webbrowser
import glob
import re

def main():
    # 加载 .env 文件
    load_dotenv()

    # 从 .env 文件中获取 Special 变量并分割
    special_names = re.split(r'[，,]', os.getenv('CHI_KEYWORD'))

    # 设置 CSV 文件目录
    data_dir = os.path.join(os.getenv('DATA_DIR'), 'csv')

    # 查找所有以 _DINO_results.csv 结尾的文件
    file_paths = glob.glob(os.path.join(data_dir, '*_DINO_results.csv'))

    # 创建保存子 HTML 文件的文件夹
    output_dir = 'temp_html_files'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 保存生成的HTML文件名
    html_files = []

    # 颜色调色板
    color_palette = ['blue', 'red', 'green', 'purple', 'orange']

    # 遍历每个找到的文件路径
    for file_path in file_paths:
        # 读取CSV文件
        data = pd.read_csv(file_path, encoding='ISO-8859-1')
        
        # 将 time 列转换为 datetime 类型
        data['time'] = pd.to_datetime(data['time'], format='%Y-%m-%d %H-%M-%S', errors='coerce')

        # # 聚合数据到每10秒
        # data = data.set_index('time')
        # data = data.resample('10S').sum().reset_index()

        # 定义要排除的列
        excluded_categories = ['Mart', 'car', 'motorcycle', 'person', 'license-plate', 'doorplate', 'street-signs']

        # 获取要绘制的列
        columns_to_plot = [col for col in data.columns if col not in excluded_categories and col != 'time']

        # 为每个类别生成单独的图表并保存为HTML文件
        for i, column in enumerate(columns_to_plot):
            fig = go.Figure()
            fig.add_trace(go.Scattergl(
                x=data['time'], 
                y=data[column], 
                mode='lines+markers', 
                name=special_names[i],
                line=dict(color=color_palette[i % len(color_palette)], width=2),
                marker=dict(
                    size=[0 if y_val == 0 else 10 for y_val in data[column]],  # 当 y=0 时设置标记大小为5，否则为10
                ),
                opacity=1,
                hovertemplate='數量: %{y}<extra></extra>',  # 自定义悬停内容
                hoverlabel=dict(namelength=0)
            ))
            
            # 设置图表标题和标签
            fig.update_layout(
                title=f'{special_names[i]} 物件偵測圖 - {os.path.basename(file_path)}',
                xaxis_title='時間',
                yaxis_title='出現數量',
                height=500,
                font=dict(size=15),  # 调整整体字体大小
                showlegend=True,
                hovermode='x unified',
                xaxis=dict(
                    title_font=dict(size=20),  # 调整X轴标题字体大小
                    rangeslider=dict(visible=True),
                    type="date",
                    rangeselector=dict(
                        buttons=list([
                            dict(count=5,
                                label="5m",
                                step="minute",
                                stepmode="backward"),
                            dict(count=10,
                                label="10m",
                                step="minute",
                                stepmode="backward"),
                            dict(count=30,
                                label="30m",
                                stepmode="backward"),
                            dict(step="all",
                                label="全部")
                        ])
                    ),
                ),
                yaxis=dict(
                    title_font=dict(size=20)  # 调整Y轴标题字体大小
                )
            )
            
            # 保存为单独的HTML文件
            output_file = os.path.join(output_dir, f'{special_names[i]}_物件偵測圖_{os.path.basename(file_path)}.html')
            plot(fig, filename=output_file, auto_open=False)
            html_files.append(output_file)


    # 合并所有HTML文件
    final_output_file = os.path.join(os.getenv('DATA_DIR'), '..', '生成圖表', '物件偵測圖表.html')
    with open(final_output_file, 'w', encoding='utf-8') as outfile:
        for fname in html_files:
            with open(fname, encoding='utf-8') as infile:
                outfile.write(infile.read())
                outfile.write("\n")
        
        # 在最后添加文件保存路径
        outfile.write(f"<div style='text-align: center; margin-top: 20px; font-size: 16px;'>")
        outfile.write(f"文件儲存路徑: {os.path.abspath(final_output_file)}")  # 动态获取文件保存路径
        outfile.write(f"</div>")

    # 删除临时的子 HTML 文件和文件夹
    shutil.rmtree(output_dir)

    # 打开合并后的HTML文件
    webbrowser.open_new_tab(final_output_file)