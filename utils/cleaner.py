# -*- coding: utf-8 -*-
import re

def clean_html_text(raw_text):
    """
    清洗从网页中提取的纯文本，去除多余的空白字符和不可见乱码
    """
    if not raw_text:
        return ""
    
    # 将多个连续的空白字符（包括空格、换行、制表符等）替换为一个单空格
    cleaned_text = re.sub(r'\s+', ' ', raw_text)
    
    # 去除首尾的空白字符
    cleaned_text = cleaned_text.strip()
    
    return cleaned_text