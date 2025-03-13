import os

def replace_first_char():

    file_path = os.path.join(os.getenv('DATA_DIR'), 'reid', 'reid_output.txt')

    if not os.path.exists(file_path):
        return 'not exist'
    else:
        # 打開文件並讀取所有行
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # 將每行的第一個字替換為 '1'
        modified_lines = []
        for line in lines:
            if line.strip():  # 確保不處理空行
                modified_line = '1' + line[1:]
                modified_lines.append(modified_line)
            else:
                modified_lines.append(line)  # 保留空行
        
        # 將修改後的內容寫回文件
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(modified_lines)

        return 'success'