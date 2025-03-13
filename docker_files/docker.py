import docker
import os
from dotenv import load_dotenv, set_key
import tools.dino_modify as dino_modify

load_dotenv()
root_dir = os.getenv('DATA_DIR')
input_videos_path = os.path.join(os.getenv('DATA_DIR'), 'input_videos')
reid_path = os.path.join(os.getenv('DATA_DIR'), 'reid')
csv_path = os.path.join(os.getenv('DATA_DIR'), 'csv')
datetime_path = os.path.join(os.getenv('DATA_DIR'), 'datetime.csv')
frames_path = os.path.join(os.getenv('DATA_DIR'), 'video_frames')
single_path = os.path.join(os.getenv('DATA_DIR'), 'single_reid')

dino_client = docker.from_env()

def reid():
    client = docker.from_env()
    container = client.containers.run(
        image='bernice1357/reid:latest',
        detach=True,
        tty=True,
        volumes={
            single_path: {'bind': '/main/single_reid', 'mode': 'rw'},
            input_videos_path: {'bind': '/main/input_videos', 'mode': 'rw'}, # 輸入影片
            reid_path: {'bind': '/main/reid', 'mode': 'rw'}, # 輸出csv
        },
        device_requests=[
            docker.types.DeviceRequest(device_ids=["0"], capabilities=[['gpu']])
        ]
    )

    if os.getenv('SINGLE_REID')=='1':
        _, output = container.exec_run(
            cmd="sh -c 'cd /main/PaddleDetection; python deploy/pipeline/pipeline.py --config deploy/pipeline/config/infer_cfg_pphuman.yml --video_dir=/main/single_reid/ --device=gpu; python modify_mtmct.py'",
        )
        print('SINGLE_REID')

    elif os.getenv('SINGLE_REID')=='0':
        _, output = container.exec_run(
            cmd="sh -c 'cd /main/PaddleDetection; python deploy/pipeline/pipeline.py --config deploy/pipeline/config/infer_cfg_pphuman.yml --video_dir=/main/input_videos/ --device=gpu; python modify_mtmct.py'",
        )
        print('input_videos')

    container.stop()
    container.remove()

def yolo_ocr():
    client = docker.from_env()
    container = client.containers.run(
        image='bernice1357/yolo_ocr:latest',
        detach=True,
        tty=True,
        volumes={
            input_videos_path: {'bind': '/main/input_videos', 'mode': 'rw'}, # 輸入影片
            datetime_path: {'bind': '/main/datetime.csv', 'mode': 'rw'}, # 輸入日期時間csv
            frames_path: {'bind': '/main/video_frames', 'mode': 'rw'}, # 輸出frames
            csv_path: {'bind': '/main/csv', 'mode': 'rw'} # 輸出 csv
        },
        device_requests=[
            docker.types.DeviceRequest(device_ids=["0"], capabilities=[['gpu']])
        ]
    )
    _, output = container.exec_run(
        cmd="sh -c 'cd /main; python3 ./yolo_main.py --i /main/video_frames --o /main/csv'",
        # stream=True # 讓輸出可以即時，不會執行完才一次輸出全部 (True:exit_code輸出none, False:exit_code輸出0)
    )

    container.stop()
    container.remove()

def dino(target):

    global dino_client
    containers = dino_client.containers.list(all=True)
    # 檢查是否有容器名稱匹配
    if len(containers)==0:
        container = dino_client.containers.run(
            image='bernice1357/dino:latest',
            name='dino123',
            detach=True,
            tty=True,
            volumes={
                frames_path: {'bind': '/opt/program/video_frames', 'mode': 'rw'}, # 輸入 frames
                csv_path: {'bind': '/opt/program/csv', 'mode': 'rw'} # 輸出 csv
            },
            device_requests=[
                docker.types.DeviceRequest(device_ids=["0"], capabilities=[['gpu']])
            ]
        )

        length = len(target)
        target = ' '.join(target)
        cmd="sh -c 'cd /opt/program/GroundingDINO; python3 dino_test.py --i /opt/program/video_frames --o /opt/program/csv --prompt {}'".format(target)
        _, output = container.exec_run(
            cmd=cmd
        )
        if length==1:
            dino_modify.process_dino_files(csv_path)

    else:
        container = dino_client.containers.get('dino123')
        if container.status == 'running':
            print("already running.")
        else:
            container.start()
            print("has been started.")

        length = len(target)
        target = ' '.join(target)
        cmd="sh -c 'cd /opt/program/GroundingDINO; python3 dino_test.py --i /opt/program/video_frames --o /opt/program/csv --prompt {}'".format(target)
        _, output = container.exec_run(
            cmd=cmd
        )
        if length==1:
            dino_modify.process_dino_files(csv_path)

def normal_rag(question):
    client = docker.from_env()
    container = client.containers.run(
        image='bernice1357/rag:latest',
        detach=True,
        tty=True,
        volumes={
            csv_path: {'bind': '/RAG/csv', 'mode': 'rw'}, # 輸入csv
            "D:/ai_contest/VIChatBot/rag": {'bind': '/RAG/test', 'mode': 'rw'}
        }
    )
    cmd = 'sh -c "cd /RAG; python normal_agent.py --a {} --i {} --api {}"'.format(os.getenv('ACTION'), question, os.getenv('API_KEY'))
    _, output = container.exec_run(
        cmd=cmd
    )
    val = output.decode('utf-8').split('\n')
    print('val', val)

    for index, elem in enumerate(val):
        if '代理回答' in elem:
            result = ''.join(val[index:-1])
    # input = val[-2].replace(' ','@')
    input = result.replace(' ','@')

    print('input', input)

    cmd = 'sh -c "cd /RAG/test; python translate.py --i {}"'.format(input)
    _, output = container.exec_run(
        cmd=cmd
    )
    val = output.decode('utf-8').split('\n')
    print('22222222222222222', val)

    container.stop()
    container.remove()

    if '代理回答' in val[-2]:
        return val[-2][11:]
    else:
        return '出現問題，請再試一次'

def dino_rag(question):

    client = docker.from_env()
    container = client.containers.run(
        image='bernice1357/rag:latest',
        detach=True,
        tty=True,
        volumes={
            csv_path: {'bind': '/RAG/csv', 'mode': 'rw'}, # 輸入csv
            "D:/ai_contest/VIChatBot/rag": {'bind': '/RAG/test', 'mode': 'rw'}
        }
    )

    cmd = 'sh -c "cd /RAG; python keyword_DINO.py --i {}"'.format(question)
    _, output = container.exec_run(
        cmd=cmd
    )
    val = output.decode('utf-8').split('\n')
    dino_input = val[-2].replace(' ', '_')
    dino([dino_input])

    cmd = 'sh -c "cd /RAG; python agent_DINO.py --i {} --api {}"'.format(question, os.getenv('API_KEY'))
    _, output = container.exec_run(
        cmd=cmd
    )
    val = output.decode('utf-8').split('\n')
    input = val[-2].replace(' ','@')
    print('111111111111111', input)

    cmd = 'sh -c "cd /RAG/test; python translate.py --i {}"'.format(input)
    _, output = container.exec_run(
        cmd=cmd
    )
    val = output.decode('utf-8').split('\n')
    print('22222222222222222', val)

    container.stop()
    container.remove()

    if '代理回答' in val[-2]:
        return val[-2][11:]
    else:
        return '出現問題，請再試一次'

def translate_keyword(keyword):
    client = docker.from_env()
    container = client.containers.run(
        image='bernice1357/rag:latest',
        detach=True,
        tty=True
    )
    cmd = 'sh -c "cd /RAG; python translate.py --i {}"'.format(keyword)
    _, output = container.exec_run(
        cmd=cmd
    )

    val = output.decode('utf-8').split('\n')

    container.stop()
    container.remove()

    return val[-2]

def remove_containers():
    client = docker.from_env()
    containers = client.containers.list(all=True)
    if len(containers)!=0:
        for container in containers:
            container.stop()
            container.remove()
            print(f"Container ID: {container.id}, Name: {container.name}, Status: {container.status}")