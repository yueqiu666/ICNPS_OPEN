import json
import os
import sys
import time
import random
from datetime import datetime

# 确保可以导入 modules 和 utils
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from modules.scraper import fetch_incremental_notices
from modules.llm_processor import LLMProcessor
from modules.mailer import Mailer
from utils.file_manager import load_history

def main():
    # 1. 加载配置
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # 2. 自动化逻辑：延迟与运行锁
    lock_file = config["app"]["lock_file"]
    today_str = datetime.now().strftime("%Y-%m-%d")

    # A. 开机延迟：等待 10 分钟 (600秒)
    delay_seconds = 600
    print(f"⏳ 自动化任务启动：系统将在 {delay_seconds // 60} 分钟后开始运转...")
    time.sleep(delay_seconds)

    # B. 每日运行锁：检查今天是否已经运行过
    if os.path.exists(lock_file):
        with open(lock_file, "r") as f:
            if f.read().strip() == today_str:
                print(f"📅 今日 ({today_str}) 已执行过推送任务，系统退出。")
                return

    # 3. 初始化核心组件
    history_file = config["app"]["history_file"]
    history_set = load_history(history_file)
    processor = LLMProcessor(config)
    mailer = Mailer(config)

    # 4. 执行爬虫模块
    print(f"🕸️ 正在巡查校园网站 (目标: 近 {config['app']['days_to_crawl']} 天通知)...")
    all_raw_notices = []
    for site_name, site_config in config["sites"].items():
        # 直接传入 test=False，让爬虫保持优雅的随机延迟防封
        results = fetch_incremental_notices(
            site_name, 
            site_config, 
            config["app"]["days_to_crawl"], 
            history_set, 
            history_file, 
            test=False
        )
        all_raw_notices.extend(results)

    # 5. 大模型智能分析 (摘要 + 打分)
    high_value_results = []
    if all_raw_notices:
        print(f"🧠 发现 {len(all_raw_notices)} 条新动态，正在启动模型进行智能分析...")
        summarized_list = []
        for n in all_raw_notices:
            # 将部门和标题拼接在一起
            full_title = f"[{n.get('dept', '未知部门')}] {n['title']}"
            
            # 阶段一：生成摘要 
            summary = processor.summarize_article(full_title, n["content"])
            if summary:
                summarized_list.append({
                    "title": full_title, 
                    "summary": summary,
                    "link": n["link"],
                    "date": n["date"]
                })

        # 阶段二：根据画像批量打分并过滤
        scored_notices = processor.score_notices(summarized_list)
        
        # 将摘要和日期等信息补回给打分结果
        for score_item in scored_notices:
            clean_score_title = score_item["title"].strip()
            
            # 模糊匹配逻辑
            match = next((item for item in summarized_list if clean_score_title in item["title"] or item["title"] in clean_score_title), None)
            
            if match:
                score_item.update({
                    "summary": match["summary"],
                    "link": match["link"],
                    "date": match["date"]
                })
            else:
                print(f"⚠️ 警告：大模型返回的标题 '{clean_score_title}' 无法与原列表匹配，可能会丢失日期和链接。")
        high_value_results = scored_notices
    else:
        print("📭 暂未发现新的校内通知。")

    # 6. 邮件推送
    print("📧 正在生成并发送通知邮件...")
    mailer.send_notice_email(high_value_results)

    # 7. 更新运行锁
    os.makedirs(os.path.dirname(lock_file), exist_ok=True)
    with open(lock_file, "w") as f:
        f.write(today_str)
    print(f"✅ 任务完成，已更新运行锁：{today_str}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 用户手动停止了系统。")
    except Exception as e:
        print(f"💥 系统运行出错: {e}")