import cv2
import os
from PIL import Image

def convert_to_png(input_path, output_dir, roi_color):
    # 讀取圖片
    image = Image.open(input_path)
    pixels = image.load()

    # 確保輸出目錄存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 定義顏色
    if '藍' in roi_color:
        new_color = (0, 142, 204)  # BGR格式的藍色
    elif '紅' in roi_color:
        new_color = (221, 0, 4)  # BGR格式的紅色
    else:
        print('未畫框')
        return

    black=(0,0,0,0)
    for y in range(image.height):
        for x in range(image.width):
            if pixels[x, y] != black:  # 只处理不是黑色的像素
                pixels[x, y] = new_color  # 替换为新颜色

    # 確保輸出路徑以 'roi_box.png' 結尾
    output_image_path = os.path.join(output_dir, 'roi_box.png')
    image.save(output_image_path)