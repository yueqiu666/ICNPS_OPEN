# -*- coding: utf-8 -*-
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timedelta
import re
import urllib3
import time
import random
from utils.cleaner import clean_html_text
from utils.file_manager import append_to_history

# 禁用 HTTPS 证书警告（部分学校校园网会有证书问题）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def parse_and_clean_date(date_str):
    """
    处理时间格式，将“昨天 16:43”或“2026-03-26”统一转化为 datetime.date 对象
    """
    today = datetime.today()
    
    if "今天" in date_str:
        return today.date()
    elif "昨天" in date_str:
        return (today - timedelta(days=1)).date()
    elif "前天" in date_str:
        return (today - timedelta(days=2)).date()
    else:
        # 正则提取 YYYY-MM-DD
        match = re.search(r'\d{4}-\d{2}-\d{2}', date_str)
        if match:
            return datetime.strptime(match.group(), '%Y-%m-%d').date()
    return None
def fetch_article_content(url, session, content_selector, test):
    """
    进入详情页抓取正文内容
    """
    try:
        if not test:
            # 优雅地休息一下，防止被封 IP
            sleep_time = random.uniform(1, 3)
            print(f"    ⏳ 稍作休息 {sleep_time:.1f} 秒...")
            time.sleep(sleep_time)
        
        # 这里用 session 发请求，它会自动带上登录状态！
        response = session.get(url, timeout=10, verify=False)
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取正文
        content_el = soup.select_one(content_selector)
        if content_el:
            raw_text = content_el.get_text(separator=' ', strip=True)
            return clean_html_text(raw_text)
        else:
            print("    ⚠️ 未能在正文页找到目标内容元素。")
            return ""
    except Exception as e:
        print(f"    ❌ 抓取正文失败: {e}")
        return ""
def fetch_incremental_notices(site_name, site_config, days_to_crawl, history_set, history_file, test, crawl_mode="compare"):
    """
    根据配置抓取单个站点的增量通知，并包含去重与正文抓取。
    crawl_mode:
    - compare: 默认模式，只做“与历史链接差集”比较，不按时间截断。
    - time_window: 兼容旧模式，结合 days_to_crawl 进行时间窗口抓取。
    """
    notices = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
    }
    
    if site_config.get("needs_cookie"):
        headers["Cookie"] = site_config.get("cookie_string", "")

    # 创建一个 Session 对象，专门用来对付需要登录的网站
    session = requests.Session()
    
    if site_config.get("needs_cookie"):
        headers["Cookie"] = site_config.get("cookie_string", "")
        # 把 Cookie 喂给 Session
        session.headers.update(headers)
    else:
        session.headers.update(headers)

    max_pages = 5 
    
    for page in range(1, max_pages + 1):
        url_template = site_config.get("url")
        url = url_template.format(page=page) if "{page}" in url_template else url_template
        
        print(f"⏳ 正在抓取 [{site_name}] 第 {page} 页列表...")
        
        try:
            response = session.get(url, timeout=10, verify=False)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            items = soup.select(site_config["list_selector"])
            if not items:
                print(f"❌ [{site_name}] 未解析到列表元素，跳出抓取。")
                break
                
            stop_pagination = False
            
            for item in items:
                title_el = item.select_one(site_config["title_selector"])
                time_el = item.select_one(site_config["time_selector"])
                
                if not title_el or not time_el:
                    continue
                    
                title = title_el.get_text(strip=True)
                link = urljoin(url, title_el.get("href", ""))
                raw_time = time_el.get_text(strip=True)
                
                pub_date = parse_and_clean_date(raw_time)

                # 【第一关】：可选的时间窗口模式（默认关闭）
                if crawl_mode == "time_window":
                    if not pub_date:
                        # 旧模式下遇到无法解析的日期，不再直接丢弃，改为保守保留
                        pub_date_str = raw_time if raw_time else "未知时间"
                    else:
                        delta = datetime.today().date() - pub_date

                        if delta.days > days_to_crawl:
                            if "[置顶]" in title:
                                print(f"  ⏭️ 跳过历史置顶: {title[:15]}...")
                                continue
                            else:
                                print(f"🛑 发现超出 {days_to_crawl} 天的普通通知 ({pub_date})，停止翻页。")
                                stop_pagination = True
                                break
                
                # ==========================================
                # 【第二关】：查重！(就是加在了这里)
                # ==========================================
                if link in history_set:
                    print(f"  ⏩ 发现已处理过，跳过: {title[:15]}...")
                    continue

                # ==========================================
                # 【第三关】：提取信息并抓取正文
                # ==========================================
                dept = "未知部门"
                if "dept_selector" in site_config:
                    dept_el = item.select_one(site_config["dept_selector"])
                    if dept_el:
                        dept = dept_el.get_text(strip=True)

                pub_date_str = str(pub_date) if pub_date else (raw_time if raw_time else "未知时间")

                print(f"  ✅ 发现新通知: {pub_date_str} | [{dept}] {title}")
                print("    -> 准备抓取正文...")
                
                article_content = fetch_article_content(link, session, site_config["content_selector"], test=test)

                if not article_content:
                    article_content = "正文抓取失败，建议点击原文查看。"

                notices.append({
                    "site": site_name,
                    "dept": dept,
                    "title": title,
                    "date": pub_date_str,
                    "link": link,
                    "content": article_content
                })
                # 发现新链接后立即记录，避免下次重复推送同一条
                append_to_history(history_file, link)
                history_set.add(link)
                
            if stop_pagination or "{page}" not in url_template:
                break
                
        except Exception as e:
            print(f"❌ [{site_name}] 抓取异常: {e}")
            break
            
    return notices
