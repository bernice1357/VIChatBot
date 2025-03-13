import pandas as pd
import plotly.graph_objs as go
import os
import webbrowser
from dotenv import load_dotenv
import numpy as np

def main(stay_time_threshold):
    # 加载 .env 文件
    load_dotenv()

    # 加载数据
    file_path = os.path.join(os.getenv('DATA_DIR'), 'csv', 'in_out.csv')
    data = pd.read_csv(file_path, encoding='ISO-8859-1')  # 根据需要选择合适的编码格式

    # 将 'time' 列转换为 datetime 类型
    data['time'] = pd.to_datetime(data['time'], format='%Y-%m-%d %H:%M:%S', errors='coerce')

    # 将 'stay' 列的值转换为 1 或 0
    data['stay_binary'] = data['stay'].apply(lambda x: 1 if x != 0 else 0)

    # 计算时间差
    data['time_diff'] = data['time'].diff()

    # 定义时间差阈值
    time_threshold = pd.Timedelta(seconds=10)

    # 创建输出目录（如果不存在）
    output_dir = 'output_htmls'
    os.makedirs(output_dir, exist_ok=True)

    # 获取保存 HTML 文件的绝对路径
    combined_html_file = os.path.join(os.getenv('DATA_DIR'), '..', '生成圖表', '人員進出圖表.html')
    absolute_path = os.path.realpath(combined_html_file)

    # 初始化主 HTML 文件内容
    combined_html_content = f"""
    <html>
    <head><title>人員進出圖表</title></head>
    <body>
    """

    # 初始化当前数据段的索引
    start_idx = 0
    file_index = 1

    # 遍历数据，找到不连续的时间点
    for idx, row in data.iterrows():
        # 跨日和超过阈值的情况都需要分段
        if row['time_diff'] > time_threshold or idx == len(data) - 1 or row['time'].date() != data.iloc[start_idx]['time'].date():
            # 选择当前时间段的数据
            current_data = data.iloc[start_idx:idx]
            
            # 计算当前时间段内的总进出人数
            total_in = current_data['in'].sum()
            total_out = current_data['out'].sum()

                    # 计算当前时间段内的最大进出人数（非总和）
            max_count = max(current_data['in'].max(), current_data['out'].max())
            print(max_count)

            # 根据 `stay_binary` 来设置 `stay_dynamic`，使用每个时间点的最大 `in` 或 `out` 人数
            current_data['stay_dynamic'] = current_data['stay_binary'].apply(lambda x: max_count if x == 1 else 0)

            # 如果当前时间段内有数据，则生成图表并保存为 HTML 文件
            if not current_data.empty:
                fig = go.Figure()

                fig.add_trace(go.Bar(
                    x=current_data['time'],
                    y=current_data['in'],
                    name='進入',
                    marker=dict(color='blue'),
                    hovertemplate='進入時間: %{x}<br>人數: %{y}<extra></extra>'  # 自定义悬停内容
                ))

                fig.add_trace(go.Bar(
                    x=current_data['time'],
                    y=current_data['out'],
                    name='離開',
                    marker=dict(color='red'),
                    hovertemplate='離開時間: %{x}<br>人數: %{y}<extra></extra>',  # 自定义悬停内容
                ))
                x_vals = current_data['time']
                y_vals = current_data['stay_dynamic'] -0.1
                y_vals = np.clip(y_vals, 0, None)
                              
                # 绘制黑线（完整的 stay_dynamic 数据）
                fig.add_trace(go.Scatter(
                    x=x_vals,
                    y=y_vals,
                    mode='lines',
                    line=dict(color='black', width=2),
                    hovertemplate=(
                        '時間: %{x}<br>'
                        '人員在ROI內: %{customdata}<br>'
                    ),
                    customdata=["有" if y > 0 else "無" for y in y_vals],
                    name='未超過閥值',
                    yaxis='y2'
                ))
                # 初始化 y_vals_green 为 NaN
                y_vals_green = np.full_like(y_vals, np.nan)

                # 标记 '有' 的位置
                has_people = y_vals > 0

                # 初始化变量
                start_idx = None  # 连续时间段的起始索引
                current_duration = pd.Timedelta(0)  # 当前时间段的持续时间

                for i in range(len(has_people)):
                    if has_people.iloc[i]:  # 使用 .iloc 来确保正确的索引访问
                        if start_idx is None:
                            start_idx = i  # 记录起始索引
                        if i > 0:
                            # 累加当前时间段的长度
                            current_duration += current_data['time_diff'].iloc[i]
                    else:
                        # 如果当前时刻没有人或者结束了连续段
                        if start_idx is not None and current_duration >= pd.Timedelta(seconds=stay_time_threshold):
                            # 如果持续时间超过了阈值，保留这个时间段的 y_vals
                            y_vals_green[start_idx:i] = y_vals[start_idx:i]
                        # 重置变量
                        start_idx = None
                        current_duration = pd.Timedelta(0)

                # 在最后一段时间后再次检查
                if start_idx is not None and current_duration >= pd.Timedelta(seconds=stay_time_threshold):
                    y_vals_green[start_idx:] = y_vals[start_idx:]
                    
                # 绘制绿线（符合条件的 stay_dynamic 数据）
                fig.add_trace(go.Scatter(
                    x=x_vals,
                    y=y_vals_green,
                    mode='lines',
                    line=dict(color='yellow', width=2),
                    hovertemplate=(
                        '時間: %{x}<br>'
                        '人員在ROI內: %{customdata}<br>'
                    ),
                    customdata=["有" if y > 0 else "無" for y in y_vals_green],
                    name='超過閥值',
                    yaxis='y2'
                ))



                # 添加注释来显示总进出人数，固定在图表右上角
                fig.add_annotation(
                    text=f"總進入人數: {total_in}<br>總離開人數: {total_out}",
                    xref="paper", yref="paper",  # 参考相对布局坐标
                    x=0.95, y=0.95,  # 固定在右上角（x 和 y 坐标为相对值，1 表示右上角）
                    showarrow=False,
                    align="left",
                    font=dict(size=15),
                    bordercolor="black",  # 添加边框颜色
                    borderwidth=1,  # 设置边框宽度
                    borderpad=4,  # 设置边框和文本之间的间距
                    bgcolor="white",  # 设置背景颜色为白色
                )

                # 更新图表布局，设置初始显示的时间范围和添加滑块
                fig.update_layout(
                    title=f'從 {current_data["time"].iloc[0]} 到 {current_data["time"].iloc[-1]}',
                    xaxis_title='時間',
                    yaxis_title='人數',
                    barmode='group',
                    height=500,
                    font=dict(size=15),
                    xaxis=dict(
                        title_font=dict(size=20),
                        range=[current_data["time"].iloc[0], current_data["time"].iloc[0] + pd.Timedelta(minutes=5)],
                        rangeselector=dict(
                            buttons=list([
                                dict(count=5, label='5m', step='minute', stepmode='backward'),
                                dict(count=10, label='10m', step='minute', stepmode='backward'),
                                dict(count=30, label='30m', step='minute', stepmode='backward'),
                                dict(step='all', label='All')
                            ])
                        ),
                        rangeslider=dict(visible=True),
                        type="date"
                    ),
                    yaxis=dict(
                        title_font=dict(size=20)
                    ),
                    yaxis2=dict(
                        title="人員在ROI內",
                        title_font=dict(size=20),
                        overlaying='y',
                        side='right',
                        tickvals=[0, max_count],  # 设定刻度
                        ticktext=["無", "有"],  # 显示“無”和“有”
                        range=[0, max_count],  # 限制范围，避免超出
                        ticklabelposition="outside",  # 将标签移到外侧以避免重叠
                        title_standoff=0  # 調整這個值來增加標題與軸的距離
                    )
                )


                # 临时保存为独立的 HTML 文件
                temp_html_file = os.path.join(output_dir, f'temp_chart_{file_index}.html')
                fig.write_html(temp_html_file)

                # 读取并合并到主 HTML 文件内容中
                with open(temp_html_file, 'r',encoding='utf-8') as file:  # 指定utf-8编码
                    html_content = file.read()
                    combined_html_content += f"<div>{html_content}</div><br>"

                # 删除临时 HTML 文件
                os.remove(temp_html_file)

                # 更新文件索引
                file_index += 1

            # 更新当前数据段的起始索引
            start_idx = idx

    # 将文件储存路径的注释添加到网页最下方
    combined_html_content += f"""
    <div style="text-align: center; margin-top: 50px;">
        文件儲存路徑: {absolute_path}
    </div>
    </body>
    </html>
    """

    # 保存主 HTML 文件
    with open(combined_html_file, 'w', encoding='utf-8') as file:  # 指定utf-8编码
        file.write(combined_html_content)

    # 保存主 HTML 文件后，自动在默认浏览器中打开
    webbrowser.open(f'file://{absolute_path}')

    print(f"Combined HTML file saved as {combined_html_file}")
