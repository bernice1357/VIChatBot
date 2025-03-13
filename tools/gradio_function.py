import gradio as gr
import os
import time
import shutil
import json
import ast
import multiprocessing

import tools.capture_frame as capture_frame
import tools.check_datetime as check_datetime 
import tools.datetime_to_files as datetime_to_files 
import tools.change_video_names as change_video_names 
import tools.copy_videos as copy_videos
import tools.roi_box as roi_box
import tools.merge_all_csv as merge_all_csv
import tools.inout_image as inout_image
import tools.frames as frames
import tools.split_video as split_video
import tools.modify_reid_result as modify_reid_result
import tools.dino_sheet as dino_sheet
import tools.tableALL as tableALL

import ROI.preprocess as preprocess
import ROI.roi_main as roi_main
import docker_files.docker as docker
from dotenv import load_dotenv, set_key

# 取得cache路徑
def get_cache_path(list):
    index = list[0].find("gradio")
    if index != -1:
        result_path = os.path.join(list[0][:index + len("gradio")])
    else:
        result_path = None
    
    os.environ.pop('CACHE_DIR', None)
    set_key(".env", "CACHE_DIR", result_path)
    load_dotenv()

# 初始化設定
def set_env():
    docker.remove_containers()
    load_dotenv()
    os.environ.pop('ENG_KEYWORD', None)
    set_key(".env", "ENG_KEYWORD", "")
    os.environ.pop('DATA_DIR', None)
    set_key(".env", "DATA_DIR", os.path.join(os.getcwd(), 'default_dir'))
    load_dotenv()

    if not os.path.exists(os.getenv('DATA_DIR')):
        os.mkdir(os.getenv('DATA_DIR'))
    else:
        shutil.rmtree(os.getenv('DATA_DIR'))
        os.mkdir(os.getenv('DATA_DIR')) 

    if not os.path.exists(os.getenv('CACHE_DIR')):
        os.mkdir(os.getenv('CACHE_DIR'))
    else:
        shutil.rmtree(os.getenv('CACHE_DIR'))
        os.mkdir(os.getenv('CACHE_DIR')) 

def show_keyword_input(action):
    if '物件偵測' in action:
        return gr.update(visible=True)
    else:
        return gr.update(visible=False)

def show_keyword_input(action):
    if '物件偵測' in action:
        return gr.update(visible=True)
    else:
        return gr.update(visible=False)

# tab1-檢查 dataframe 跟 checkbox 有無缺值
def tab1_process_data(files, checkbox, dataframe, keyword):

    # 錯誤判斷
    if not checkbox and (dataframe == "").values.any():
        raise gr.Error("執行功能及影片資訊尚未填寫完畢!", duration=3)
    elif not checkbox:
        raise gr.Error("欲執行功能尚未選擇!", duration=3)
    elif (dataframe == "").values.any():
        raise gr.Error("影片資訊尚未填寫完畢!", duration=3)
    elif check_datetime.check_datetime(dataframe):
        raise gr.Error("影片資訊格式有誤!", duration=3)

    # 開始處理
    os.environ.pop('ACTION', None)
    if len(checkbox)==2:
        gr.Info("等待數據處理中，請勿關閉分頁", duration=0)
        set_key(".env", "ACTION", "both")
        # 設定中文關鍵字
        os.environ.pop('CHI_KEYWORD', None)
        set_key(".env", "CHI_KEYWORD", keyword)
        load_dotenv()

        get_cache_path(files)

        # 改變影片檔名+回傳新list和dataframe
        new_files, new_df = change_video_names.main(files, dataframe)
        # 輸出日期時間為 csv，儲存檔案至指定路徑
        datetime_to_files.main(new_files, new_df)
        # 複製影片到新目錄
        copy_videos.copy_videos(os.getenv('CACHE_DIR'), os.getenv('DATA_DIR')+"/input_videos")

        if len(files)==1:
            split_video.main(new_files[0])
            os.environ.pop('SINGLE_REID', None)
            set_key(".env", "SINGLE_REID", "1")
            load_dotenv()
            print(os.getenv('SINGLE_REID'))

        if len(keyword)!=0:
            trans_keyword = docker.translate_keyword(keyword)
            os.environ.pop('ENG_KEYWORD', None)
            set_key(".env", "ENG_KEYWORD", json.dumps(trans_keyword))
            load_dotenv()

        capture_frame.capture_frame(new_files) # 畫電子圍籬要的圖片
        gr.Info("請於此頁面繪製電子圍籬", duration=0)
        return (gr.update(interactive=False), 
                gr.update(interactive=True), 
                gr.update(interactive=False), 
                gr.update(value=os.getenv('CACHE_DIR')+"/label_image/image.jpg"), 
                gr.update(visible=False))

    elif '人員進出' in checkbox:
        gr.Info("等待影片前處理中，請勿關閉分頁", duration=0)
        set_key(".env", "ACTION", "2")

        get_cache_path(files)

        # 改變影片檔名+回傳新list和dataframe
        new_files, new_df = change_video_names.main(files, dataframe)
        # 輸出日期時間為 csv，儲存檔案至指定路徑
        datetime_to_files.main(new_files, new_df)
        # 複製影片到新目錄
        copy_videos.copy_videos(os.getenv('CACHE_DIR'), os.getenv('DATA_DIR')+"/input_videos")

        # 是否處理拆分影片
        os.environ.pop('SINGLE_REID', None)
        if len(files)==1:
            set_key(".env", "SINGLE_REID", "1")
            split_video.main(new_files[0])
        else:
            set_key(".env", "SINGLE_REID", "0")
        load_dotenv()

        capture_frame.capture_frame(new_files) # 畫電子圍籬要的圖片
        gr.Info("請於此頁面繪製電子圍籬", duration=0)
        return (gr.update(interactive=False), 
                gr.update(interactive=True), 
                gr.update(interactive=False), 
                gr.update(value=os.getenv('CACHE_DIR')+"/label_image/image.jpg"),
                gr.update(visible=False))

    else:
        gr.Info("等待數據處理中，請勿關閉分頁", duration=0)
        set_key(".env", "ACTION", "1")
        # 設定中文關鍵字
        os.environ.pop('CHI_KEYWORD', None)
        set_key(".env", "CHI_KEYWORD", keyword)
        load_dotenv()

        get_cache_path(files)

        # 改變影片檔名+回傳新list和dataframe
        new_files, new_df = change_video_names.main(files, dataframe)
        # 輸出日期時間為 csv，儲存檔案至指定路徑
        datetime_to_files.main(new_files, new_df)
        # 複製影片到新目錄
        copy_videos.copy_videos(os.getenv('CACHE_DIR'), os.getenv('DATA_DIR')+"/input_videos")

        if len(keyword)!=0:
            trans_keyword = docker.translate_keyword(keyword)
            os.environ.pop('ENG_KEYWORD', None)
            set_key(".env", "ENG_KEYWORD", json.dumps(trans_keyword))
            load_dotenv()
            keyword = ast.literal_eval(os.getenv('ENG_KEYWORD')[1:-1])
            keyword = [item.replace(' ', '_').lower() for item in keyword]
        else:
            keyword = []
            
        frames.main() 
        docker.yolo_ocr()
        docker.dino(keyword+["car", "motorcycle","person"])
        merge_all_csv.main()

        if not os.path.exists(os.path.join(os.getenv('DATA_DIR'), '..', '生成圖表')):
            os.mkdir(os.path.join(os.getenv('DATA_DIR'), '..', '生成圖表'))

        if len(keyword)!=0:
            dino_sheet.main()

        tableALL.main()

    gr.Info("數據處理完成！請於此頁面進行提問", duration=0)
    return (gr.update(interactive=False), 
            gr.update(interactive=False), 
            gr.update(interactive=True), 
            gr.update(interactive=False), 
            gr.update(visible=False))
        
# tab2-判斷是否畫框
def draw_roi(editor, color):
    roi_box.convert_to_png(editor['layers'][0], os.getenv('DATA_DIR'), color)

# tab2-送出
def tab2_process_data(editor, threshold, stay_threshold, color):
    if color is None:
        raise gr.Error("尚未選擇畫框顏色", duration=3)
    else:
        # 開始處理
        gr.Info("等待數據處理中，請勿關閉分頁", duration=0)
        draw_roi(editor, color)

        if os.getenv('ACTION')=='2':
            docker.reid()
            if os.getenv('SINGLE_REID')=='1':
                # result = modify_reid_result.replace_first_char()
                mode='single'
                file_path = os.path.join(os.getenv('DATA_DIR'), 'reid', 'reid_output.txt')
                if not os.path.exists(file_path):
                    raise gr.Error("影片沒有辨識到人員進出！請再次確認影片內容", duration=0)

                os.environ.pop('SINGLE_REID', None)
                set_key(".env", "SINGLE_REID", "0")
                load_dotenv()
            else:
                mode='normal'
                file_path = os.path.join(os.getenv('DATA_DIR'), 'reid', 'reid_output.txt')
                if not os.path.exists(file_path):
                    raise gr.Error("影片沒有辨識到人員進出！請再次確認影片內容", duration=0)
                
            preprocess.main(mode)
            roi_main.main(threshold)
        elif os.getenv('ACTION')=='both':
            # 人員進出
            docker.reid()
            if os.getenv('SINGLE_REID')=='1':
                result = modify_reid_result.replace_first_char()
                if 'not exist' in result:
                    print('not exist')
                    raise gr.Error("影片沒有辨識到人員進出！請再次確認影片內容", duration=0)
                
                os.environ.pop('SINGLE_REID', None)
                set_key(".env", "SINGLE_REID", "0")
                load_dotenv()
            preprocess.main()
            roi_main.main(threshold)

            # 物件偵測
            frames.main()
            docker.yolo_ocr()
            docker.dino(["car", "motorcycle","person"])
            merge_all_csv.main()

        # 畫人員進出圖表
        inout_image.main(stay_threshold)

        gr.Info("數據處理完成！請在此頁面進行提問", duration=0)
        return gr.update(interactive=False), gr.update(interactive=True)

# tab1-清除上傳影片
def clear_videos():
    shutil.rmtree(os.getenv('CACHE_DIR'))
    shutil.rmtree(os.getenv('DATA_DIR'))
    if not os.path.exists(os.getenv('DATA_DIR')):
        os.mkdir(os.getenv('DATA_DIR'))
    return gr.update(interactive=True, value=None), gr.update(interactive=False, value=[], row_count=(15,'fixed'))

# tab1-上傳影片轉成日期時間
def videos_to_datetime(files):
    # 沒傳檔案就送出
    if not files:
        return gr.update(interactive=True), gr.update(interactive=False)
    # 有傳檔案
    else:
        output=[]
        for file_name in files:
            file_name = os.path.basename(file_name)
            file_name, ext = os.path.splitext(file_name)[0], os.path.splitext(file_name)[1]
            output.append([file_name+ext, '', ''])
        return gr.update(interactive=False), gr.update(interactive=True, value=output, row_count=(len(files),'fixed'))

# tab2-重新選擇檔案
def tab2_to_tab1_func():
    shutil.rmtree(os.getenv('CACHE_DIR'))
    shutil.rmtree(os.getenv('DATA_DIR'))
    if not os.path.exists(os.getenv('DATA_DIR')):
        os.mkdir(os.getenv('DATA_DIR'))

    return gr.update(interactive=True), gr.update(interactive=False), gr.update(interactive=True, value=None), gr.update(interactive=False, value=[], row_count=(15,'fixed')), gr.update(value=None), gr.update(interactive=True), gr.update(interactive=True)

# tab3-設定api
def set_api_key(new_api):
    os.environ.pop('API_KEY', None)
    set_key(".env", "API_KEY", new_api)
    load_dotenv()

# tab3-重新選擇檔案
def tab3_to_tab1_func():
    shutil.rmtree(os.getenv('CACHE_DIR'))
    shutil.rmtree(os.getenv('DATA_DIR'))
    if not os.path.exists(os.getenv('DATA_DIR')):
        os.mkdir(os.getenv('DATA_DIR'))

    return gr.update(interactive=True), gr.update(interactive=False), gr.update(interactive=True, value=None), gr.update(interactive=False, value=[], row_count=(15,'fixed')), gr.update(value=None), gr.update(interactive=True), gr.update(interactive=True)

# tab3-對話提交問題
def show_question(state, question):
    if not os.getenv('API_KEY'):
        raise gr.Error("尚未填寫 API 金鑰!", duration=0)
    else:
        state['chat_history'].append((question,None))
        return state['chat_history'], state

def show_response(state, question, dino_btn):
    
    if dino_btn==False:
        print('normal')
        response = docker.normal_rag(question)
        state['chat_history'].append((None,response))
        return state['chat_history'], state
    else:
        response = docker.dino_rag(question)
        state['chat_history'].append((None,response))
        return state['chat_history'], state