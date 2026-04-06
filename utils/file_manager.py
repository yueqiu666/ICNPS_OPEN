# -*- coding: utf-8 -*-
import os

# 设定历史记录最大保留条数（根据你每天抓取的通知量，500条足够覆盖大半年的增量了）
MAX_HISTORY_LINES = 500

def load_history(history_file):
    """读取已处理过的 URL 列表，并包含自动清理机制"""
    if not os.path.exists(history_file):
        return set()
        
    with open(history_file, 'r', encoding='utf-8') as f:
        # 读取所有非空行
        lines = [line.strip() for line in f if line.strip()]
        
    # 🌟 触发自动清理机制
    if len(lines) > MAX_HISTORY_LINES:
        print(f"🧹 历史记录超过 {MAX_HISTORY_LINES} 条，正在执行自动清理瘦身...")
        # 因为最新的通知总是追加在文件末尾，所以我们只保留最后 MAX_HISTORY_LINES 条
        lines = lines[-MAX_HISTORY_LINES:]
        
        # 将截断后的最新记录重新覆盖写入文件
        with open(history_file, 'w', encoding='utf-8') as f:
            for line in lines:
                f.write(f"{line}\n")
                
    # 转换并返回集合，查找速度极快
    return set(lines)

def append_to_history(history_file, url):
    """将新 URL 追加到日志文件中"""
    # 确保 data 文件夹存在
    os.makedirs(os.path.dirname(history_file), exist_ok=True)
    with open(history_file, 'a', encoding='utf-8') as f:
        f.write(f"{url}\n")
