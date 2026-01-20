'''
Author: wlaten
Date: 2026-01-12 15:54:46
LastEditTime: 2026-01-20 17:11:36
Discription: file content
'''
import os
import logging
import requests
from email.mime.text import MIMEText
import smtplib
from config import get_config

logger = logging.getLogger(__name__)

def send_github_issue(title, content) -> bool:
    """
    发送 GitHub Issue 通知（这个不需要配置）
    """
    try:
        token = get_config("GITHUB_TOKEN")
        repo = get_config("GITHUB_REPOSITORY")
        
        if not token or not repo:
            logger.debug("这是github环境吗就跑这个？？？")
            return False
        
        url = f"https://api.github.com/repos/{repo}/issues"
        resp = requests.post(
            url,
            headers={
                "Authorization": f"token {token}"
            },
            json={
                "title": title,
                "body": content
            },
            timeout=10,
        )
        resp.raise_for_status()
        logger.info("GitHub Issue 通知发送成功")
        return True
    except Exception as e:
        logger.error(f"GitHub Issue 通知发送失败: {e}")
        return False

def send_email(title, content) -> bool:
    """
    发送邮件通知（这个要配置）
    """
    try:
        required = ["EMAIL_HOST",
                    "EMAIL_PORT",
                    "EMAIL_USER", 
                    "EMAIL_PASSWORD", 
                    "EMAIL_TO"]
        if not all(get_config(k, None) for k in required):
            logger.error("邮件通知未配置完整，跳过发送")
            return False    # 没配置邮箱
        
        host = get_config("EMAIL_HOST")
        port = int(get_config("EMAIL_PORT"))
        user = get_config("EMAIL_USER")
        password = get_config("EMAIL_PASSWORD")
        addr = get_config("EMAIL_TO")
        
        msg = MIMEText(content.replace('\n', '<br>'), 'html', 'utf-8')
        msg["Subject"] = title
        msg["From"] = user
        msg["To"] = addr
        
        server = smtplib.SMTP_SSL(host, port) if port == 465 else smtplib.SMTP(host, port)
        if port != 465:
            server.starttls()
            
        server.login(user, password)
        server.send_message(msg)
        server.quit()
        
        logger.info("邮件通知发送成功")
        return True
        
    except Exception as e:
        logger.debug(f"邮件通知发送失败: {e}")
        return False
    
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    send_email("测试邮件", "这是一封测试邮件。")