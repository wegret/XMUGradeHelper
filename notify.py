'''
Author: wlaten
Date: 2026-01-12 15:54:46
LastEditTime: 2026-01-12 16:34:52
Discription: file content
'''
import os
import logging
import requests
from email.mime.text import MIMEText
import smtplib

logger = logging.getLogger(__name__)

try:
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    pass

def send_github_issue(title, content) -> bool:
    """
    发送 GitHub Issue 通知（这个不需要配置）
    """
    try:
        token = os.getenv("GITHUB_TOKEN")
        repo = os.getenv("GITHUB_REPOSITORY")
        
        if not token or not repo:
            logging.error("这是github环境吗就跑这个？？？")
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
        if not all(os.getenv(k) for k in required):
            logger.error("邮件通知未配置完整，跳过发送")
            return False    # 没配置邮箱
        
        host = os.getenv("EMAIL_HOST")
        port = int(os.getenv("EMAIL_PORT"))
        user = os.getenv("EMAIL_USER")
        password = os.getenv("EMAIL_PASSWORD")
        addr = os.getenv("EMAIL_TO")
        
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
        logging.error(f"邮件通知发送失败: {e}")
        return False
    
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    send_email("测试邮件", "这是一封测试邮件。")