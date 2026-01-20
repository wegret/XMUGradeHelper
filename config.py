'''
Author: wlaten
Date: 2026-01-20 16:29:44
LastEditTime: 2026-01-20 18:51:57
Discription: file content
'''

import os, json
import logging

logger = logging.getLogger(__name__)

try:
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    pass

_raw_cfg = os.getenv("CONFIG_JSON", "").strip()
_cfg = {}
if _raw_cfg:
    try:
        _cfg = json.loads(_raw_cfg)
    except Exception as e:
        logger.error(f"解析 CONFIG_JSON 失败: {e} （JSON 配置错误？）")
else:
    logger.warning("未检测到 CONFIG_JSON 环境变量")

def get_config(item: str, default=None):    # ! 返回什么类型都可以，返回后一定要主动类型转换
    val = os.getenv(item)   # 兼容第一版代码，两种配置方式都可以
    if val is not None and val.strip() != "": 
        return val 
    if item in _cfg:
        return _cfg[item]
    if default is not None:
        return default
    return None # 兼容第一版代码，仿照os.getenv的行为，这里不能抛出错误
