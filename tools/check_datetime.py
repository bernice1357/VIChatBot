import pandas as pd
import re

# 定義正則表達式
DATE_PATTERN = r'^\d{4}-\d{2}-\d{2}$'
TIME_PATTERN = r'^\d{2}:\d{2}:\d{2}$'

# 定義判斷函數
def is_valid_date(date_str):
    if re.match(DATE_PATTERN, date_str):
        year, month, day = map(int, date_str.split('-'))
        try:
            pd.Timestamp(year, month, day)
            return True
        except ValueError:
            return False
    return False

def is_valid_time(time_str):
    if re.match(TIME_PATTERN, time_str):
        hour, minute, second = map(int, time_str.split(':'))
        return (0 <= hour < 24) and (0 <= minute < 60) and (0 <= second < 60)
    return False

# 主函數
def check_datetime(df):
    # 檢查日期和時間的有效性
    date_errors = df['影片發生日期'].apply(lambda x: not is_valid_date(x))
    time_errors = df['影片起始時間'].apply(lambda x: not is_valid_time(x))
    
    # 如果有任何錯誤，返回 True
    return date_errors.any() or time_errors.any()