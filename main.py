'''
Author: wlaten
Date: 2026-01-12 17:30:43
LastEditTime: 2026-01-20 18:41:22
Discription: file content
'''
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from config import get_config

from jwclient import JWClient
import notify

import os, json
os.makedirs("cache", exist_ok=True)

cache_file = "cache/grade_report.json"

def load_report():
    try:
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"加载上次成绩报告失败: {e}")
    return None

def save_report(report) -> bool:
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"保存成绩报告失败: {e}")
        return False

logs_file = "cache/record.json"

def load_logs():  # 运行记录，比如错误次数
    record = {}
    if not os.path.exists(logs_file):
        record = {
            "network_error_cnt": 0  # 目前就记录这一个，连续错误次数
        }
        with open(logs_file, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=4)
    else:
        with open(logs_file, "r", encoding="utf-8") as f:
            record = json.load(f)
    return record

def save_logs(record) -> bool:
    try:
        with open(logs_file, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"保存运行记录失败: {e}")
        return False

def compare_reports(report_old, report_new):
    """
    比较新旧成绩报告
    返回 list 更新内容，如果返回None则表示无更新
    
    # ! 这里不能直接比较总学分，因为教务系统上的学分统计好像有点问题？？？
    """
    updates = []
    
    courses_old = {c["course_name"]: c for c in report_old.get("courses", [])}
    
    for course in report_new.get("courses", []):
        if course["course_name"] not in courses_old:
            updates.append(course)
    
    return updates

def send_notification(title, content, all=False):
    if str(get_config("NOTIFY_GITHUB_ISSUE_ENABLED", "false")).lower() == "true" or all:
        notify.send_github_issue(title, content)
    notify.send_email(title, content)

def main():
    logger.info("开始检查成绩更新...")
    
    username = get_config("XMU_USERNAME")
    password = get_config("XMU_PASSWORD")
    request_interval = float(get_config("REQUEST_INTERVAL", 0.75))
    
    if not username or not password:
        logger.error("请设置环境变量 XMU_USERNAME 和 XMU_PASSWORD 以提供登录信息。")
        return 1
    
    client = JWClient(request_interval=request_interval)
    
    run_logs = load_logs()
    success, message = client.login(username, password)
    
    if not success:
        if message.startswith("网络请求发生错误"):
            run_logs["network_error_cnt"] = run_logs.get("network_error_cnt", 0) + 1
            save_logs(run_logs)
            logger.error(f"登录失败（连续错误次数 {run_logs['network_error_cnt']}）: {message}")
            error_alarm_threshold = int(get_config("NETWORK_ERROR_THRESHOLD", 5))
            if run_logs["network_error_cnt"] < error_alarm_threshold:
                return 0    # ! 错够多次后再报警（网络问题很正常）
            # 不清空错误次数，报错一次就够了
        else:
            logger.error(f"登录失败: {message}")
        return 1
    else:
        run_logs["network_error_cnt"] = 0
        save_logs(run_logs)
    
    logger.info("登录成功，正在获取成绩报告...")
    
    try:
        report = client.get_grade_report()
        logger.info("成绩报告获取成功。")
    except Exception as e:
        logger.error(f"获取成绩报告失败: {e}")
        return 1
    
    report_old = load_report()
    if report_old is None:  # 第一次运行
        
        # ! 发第一次的成绩通知，表明运行成功
        courses_newest = report.get("courses", [])[-10:] # 抓取最新10门课程来测试
        
        title = "XMU成绩监视器首次运行成功"
        
        content = "已获取当前成绩报告。\n 最新几门课程成绩：\n" + "\n".join([f"- {c['course_name']}: {c['course_grade']}" for c in courses_newest])
        
        # send_notification(title, content, all=True) # 首次运行强制发送所有通知渠道
        send_notification(title, content) # 保护隐私
        
        save_report(report)
        logger.info("首次运行，已保存当前成绩报告。")
    else:   # 正常运行
        updates = compare_reports(report_old, report)
        
        if updates:
            title = "恭喜，有新的成绩更新！"
            content = "以下是新的成绩更新：\n" + "\n".join([f"- {c['course_name']}: {c['course_grade']}" for c in updates])
            
            send_notification(title, content)
            
        else:
            logger.info("成绩无更新。")
        
        save_report(report)
        logger.info("已保存当前成绩报告。")
    
    return 0

if __name__ == "__main__":
    exit(main())