import re, argparse
from deep_translator import GoogleTranslator

def en_to_tw_force(english_text):
    # 找出所有的中文並標記
    chinese_parts = re.findall(r'[\u4e00-\u9fff]+', english_text)
    placeholder_text = re.sub(r'[\u4e00-\u9fff]+', '{}', english_text)

    # 翻譯純英文部分
    translator = GoogleTranslator(source='en', target='zh-TW')
    translated_text = translator.translate(placeholder_text)

    # 將中文部分插入回翻譯後的文本
    for chinese in chinese_parts:
        translated_text = translated_text.replace('{}', chinese, 1)

    return translated_text

# 示例文本
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--i')
    args = parser.parse_args()
    
    args.i = args.i.replace('@', ' ')

    tran_tw = en_to_tw_force(args.i)
    print("中文翻譯:", tran_tw)