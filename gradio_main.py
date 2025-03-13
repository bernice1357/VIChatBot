import gradio as gr
from gradio.themes.soft import Soft
from gradio.themes.utils import colors, fonts, sizes
from typing import Iterable
import tools.gradio_function as gradio_function
import pandas as pd
import os
from dotenv import load_dotenv

class Seafoam(Soft):
    def __init__(
        self,
        *,
        primary_hue: colors.Color | str = colors.slate,
        secondary_hue: colors.Color | str = colors.slate,
        neutral_hue: colors.Color | str = colors.slate,
        spacing_size: sizes.Size | str = sizes.spacing_md,
        radius_size: sizes.Size | str = sizes.radius_md,
        text_size: sizes.Size | str = sizes.text_lg,
        font: fonts.Font
        | str
        | Iterable[fonts.Font | str] = (
            fonts.GoogleFont("Quicksand"),
            "ui-sans-serif",
            "sans-serif",
        ),
        font_mono: fonts.Font
        | str
        | Iterable[fonts.Font | str] = (
            fonts.GoogleFont("IBM Plex Mono"),
            "ui-monospace",
            "monospace",
        ),
    ):
        super().__init__(
            primary_hue=primary_hue,
            secondary_hue=secondary_hue,
            neutral_hue=neutral_hue,
            spacing_size=spacing_size,
            radius_size=radius_size,
            text_size=text_size,
            font=font,
            font_mono=font_mono,
        )
        super().set(
            shadow_drop="rgba(60, 64, 67, 0.3) 0px 1px 2px 0px, rgba(60, 64, 67, 0.15) 0px 2px 6px 2px",
            shadow_drop_lg="0 2px 5px 0 rgb(0 0 0 / 0.1)",
            body_background_fill="#E4E6F8",
            body_background_fill_dark="#3B3B3B",
            button_primary_background_fill="linear-gradient(90deg, #4158D0 0%, #C850C0 97%)",
            button_primary_background_fill_hover="#9BABFE",
            button_primary_text_color="white",
            button_primary_background_fill_dark="linear-gradient(90deg, #4158D0 0%, #C850C0 97%)",
            slider_color="*secondary_300",
            slider_color_dark="*secondary_600",
            block_title_text_weight="1000",
            block_border_width="1px",
            block_shadow="*shadow_drop_lg",
            button_shadow="*shadow_drop_lg",
            input_shadow="*shadow_drop",
            input_shadow_focus="*shadow_drop",
            button_large_padding="9px",
            checkbox_border_color='#A1A1A1'
        )
seafoam = Seafoam()

css = """
.label{
    font-size:1.3rem !important;
}
.file_height {
    height: 580px;
}
.dataframe_height {
    height: 630px;
}
#disable * {
    pointer-events: none;
    opacity: 0.95 !important;
}
"""

# main
with gr.Blocks(theme=seafoam, css=css) as app:
    gr.Blocks.load(app, gradio_function.set_env)

    with gr.Tab("上傳檔案", elem_classes=['label']) as tab_1:
        with gr.Row():
            with gr.Column(scale=5):
                with gr.Group():
                    upload_files = gr.File(
                        file_count="multiple", 
                        height=580, 
                        label="請上傳影片格式檔案，並點選'填寫日期和時間'",
                        elem_classes=["file_height"]
                    )
                    with gr.Row():
                        clear_btn = gr.Button("重選上傳檔案")
                        upload_btn = gr.Button("填寫日期和時間", variant="primary")
                    
            with gr.Column(scale=7):
                # 日期時間表格
                df=pd.DataFrame({})
                upload_dataframe = gr.Dataframe(
                    label="日期格式: YYYY-MM-DD, 時間格式: HH:MM:SS",
                    headers=["影片名稱", "影片發生日期", "影片起始時間"],
                    datatype=["str", "str", "str"],
                    row_count=(15,'fixed'),
                    col_count=(3,'fixed'),
                    height=600,
                    column_widths=['55%','20%','25%'],
                    interactive = False,
                    elem_classes=["dataframe_height",'label']
                )
            upload_btn.click(gradio_function.videos_to_datetime, inputs=upload_files, outputs=[upload_files, upload_dataframe])
            clear_btn.click(gradio_function.clear_videos, outputs=[upload_files, upload_dataframe])

        with gr.Row():
            action = gr.CheckboxGroup(["物件偵測","人員進出"], label="欲執行功能")
            keyword = gr.Textbox(
                max_lines=1,
                label='感興趣的新類別物件(例如:穿紅色衣服的人）且以逗號分開',
                visible=False
            )
            action.input(gradio_function.show_keyword_input, inputs=action, outputs=keyword)

        tab1_submit_btn = gr.Button("開始處理檔案", variant="primary")
        
    with gr.Tab(
        "繪製電子圍籬及設定門檻值",
        interactive=False
    ) as tab_2:
        with gr.Row():
            with gr.Column(scale=2):
                image_editor = gr.ImageEditor(
                    sources=None,
                    type='filepath',
                    show_label=True,
                    label="紅色方框表示鏡頭視角在外部，藍色方框表示鏡頭視角在內部",
                    show_download_button=False,
                    interactive=True,
                    layers=False,
                    brush=gr.Brush(default_size=10, colors=['FFFFFF'],color_mode='fixed'), 
                    transforms=(),
                    eraser=gr.Eraser()
                )

            with gr.Column(scale=1):
                roi_color = gr.Dropdown(choices=['紅色 (鏡頭視角在外部)', '藍色 (鏡頭視角在內部)'], label='畫框顏色')
                threshold = gr.Number(label='人員離開ROI但還在畫面上的秒數')
                stay_threshold = gr.Number(label='人員停留的時間')
    
        with gr.Row():
            tab2_retry_btn = gr.Button("重新選擇上傳檔案")
            tab2_submit_btn = gr.Button("確認送出", variant="primary")

        tab2_retry_btn.click(gradio_function.tab2_to_tab1_func, outputs=[tab_1, tab_2, upload_files, upload_dataframe, action, tab1_submit_btn, tab2_submit_btn])

    with gr.Tab("對話機器人", interactive=False) as tab_3:
        with gr.Group():
            chatbot = gr.Chatbot(
                height=650,
                show_label=False
            )
            with gr.Row():
                with gr.Column(scale=8):
                    with gr.Group():
                        state = gr.State({'chat_history': []})
                        question = gr.Textbox(
                            placeholder="請在此輸入提問...",
                            show_label=False,
                            max_lines=1,
                            scale=9
                        )
                        dino_btn = gr.Checkbox(
                            label='追加詢問新類別物件',
                            interactive=True
                        )
                with gr.Column(scale=2):
                    chat_submit_btn =  gr.Button(
                        "送出提問",
                        scale=2,
                        variant="primary"
                    )
                
                chat_submit_btn.click(gradio_function.show_question, inputs=[state, question], outputs=[chatbot, state]).then(
                    gradio_function.show_response, inputs=[state, question, dino_btn], outputs=[chatbot, state]
                )

        with gr.Row():
            load_dotenv()
            go_tab1_btn = gr.Button("重新選擇上傳檔案", scale=2)
            api_key = gr.Textbox(
                value=os.getenv('API_KEY'), 
                label="API金鑰",
                interactive=True,
                max_lines=1,
                scale=8
            )

            api_key.blur(gradio_function.set_api_key, api_key)
    
    tab1_submit_btn.click(gradio_function.tab1_process_data, inputs=[upload_files, action, upload_dataframe, keyword], outputs=[tab_1, tab_2, tab_3, image_editor, keyword])
    tab2_submit_btn.click(gradio_function.tab2_process_data, inputs=[image_editor, threshold, stay_threshold, roi_color], outputs=[tab_2, tab_3])
    go_tab1_btn.click(gradio_function.tab3_to_tab1_func, outputs=[tab_1, tab_3, upload_files, upload_dataframe, action, tab1_submit_btn, tab2_submit_btn])

app.launch()