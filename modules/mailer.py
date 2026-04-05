import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime

class Mailer:
    def __init__(self, config):
        self.smtp_config = config["smtp"]
        self.user_name = config["app"].get("user_name", "同学")

    def send_notice_email(self, high_value_notices):
        """
        按时间排序并发送极简格式的通知邮件
        """
        today_str = datetime.now().strftime("%Y年%m月%d日")
        
        # 1. 排序逻辑：按发布时间由新及旧排序 (降序)
        # 注意：这里假设 notice 对象中包含 'date' 字段
        sorted_notices = sorted(
            high_value_notices, 
            key=lambda x: x.get('date', ''), 
            reverse=True
        )

        # 2. 构建邮件正文
        if not sorted_notices:
            # 无高价值通知时的内容
            content_body = f"<p style='color: #666;'>🔍 今日暂无个性化通知，明天再来看看吧！</p>"
        else:
            # 有高价值通知时的内容
            list_items = ""
            for i, notice in enumerate(sorted_notices, 1):
                date = notice.get('date', '未知日期')
                title = notice.get('title', '无标题')
                link = notice.get('link', '#')
                summary = notice.get('summary', '暂无摘要内容')
                reason = notice.get('reason', '暂无理由')
                
                # 按照要求格式：1. （发布时间）通知标题（点击即可跳转）：摘要。
                list_items += f"""
                <li style="margin-bottom: 15px;">
                    <strong>({date})</strong> 
                    <a href="{link}" style="color: #2E5C87; text-decoration: none;">{title} </a>：
                    <span style="color: #333;">{summary}{reason}</span>
                </li>
                """
            content_body = f"<ol style='padding-left: 20px;'>{list_items}</ol>"

        # 3. 组装完整 HTML
        html_content = f"""
        <html>
        <body style="font-family: 'Microsoft YaHei', sans-serif; max-width: 800px; margin: 20px auto;">
            <h2 style="border-bottom: 2px solid #2E5C87; padding-bottom: 10px; color: #2E5C87;">
                🎓 ICNPS 个性化校园通知推送 - {today_str}
            </h2>
            <p>你好，{self.user_name}！以下是今日为你选取的个性化推送：</p>
            {content_body}
            <hr style="border: none; border-top: 1px solid #eee; margin-top: 30px;">
            <p style="color: #999; font-size: 12px;">
                * 提示：本邮件由 ICNPS 自动化系统生成。
            </p>
        </body>
        </html>
        """

        # 4. 邮件对象设置
        message = MIMEText(html_content, 'html', 'utf-8')
        sender_nickname = "ICNPS 助手" 
        message['From'] = f"{Header(sender_nickname, 'utf-8').encode()} <{self.smtp_config['sender_email']}>"
        message['To'] = self.smtp_config["receiver_email"]
        message['Subject'] = Header(f"🎓 ICNPS 推送：{today_str}", 'utf-8')

        # 5. 执行发送
        try:
            with smtplib.SMTP_SSL(self.smtp_config["host"], self.smtp_config["port"]) as server:
                server.login(self.smtp_config["sender_email"], self.smtp_config["auth_code"])
                server.sendmail(
                    self.smtp_config["sender_email"], 
                    [self.smtp_config["receiver_email"]], 
                    message.as_string()
                )
            print(f"📧 邮件发送成功！今日包含 {len(sorted_notices)} 条高分推送。")
        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")
