'''
Author: wlaten
Date: 2026-01-10 15:24:29
LastEditTime: 2026-01-10 17:10:25
Discription: file content
'''
import os, dotenv, time
import requests
import logging
import execjs
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

dotenv.load_dotenv()

username = os.getenv("XMU_USERNAME")
password = os.getenv("XMU_PASSWORD")
request_interval = int(os.getenv("REQUEST_INTERVAL", 1))    # 请求间隔，单位秒

class JWClient:
    def __init__(self, request_interval: int = 1):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
        })  # todo 随机UA
        self.js_path = "cache/encrypt.js"
        
        self.last_request_time = 0
        self.request_interval = request_interval
    
    def _request(self,
                 method: str,
                 url: str,
                 max_retries: int = 3,
                 **kwargs) -> requests.Response:
        """
        带重试机制的底层请求封装
        :return: 成功的 Response 对象
        :raise: 超过重试次数后抛出异常，由上层捕获
        """
        kwargs.setdefault('timeout', 10)
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                if (time.time() - self.last_request_time) < self.request_interval:
                    time.sleep(self.request_interval - (time.time() - self.last_request_time))
                self.last_request_time = time.time()
                
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                last_exception = e
                logger.warning(f"请求失败 ({attempt + 1}/{max_retries}): {url} - {e}")
        
        if last_exception:
            raise last_exception
        raise requests.RequestException(f"Max retries exceeded with no specific exception: {url}")
    
    def _get_encrypt_context(self):
        """获取加密JS上下文"""
        resp = self._request("GET", "https://ids.xmu.edu.cn/authserver/qrcodeTheme/static/common/encrypt.js")
        js_code = resp.text + """
            function encryptPassword(password, salt) {
                return encryptAES(password, salt);
            }
        """
        return execjs.compile(js_code)
    
    def login(self, username: str, password: str) -> tuple[bool, str]:
        logger.info(f"正在尝试登录账号：{username}")
        
        login_url = "https://ids.xmu.edu.cn/authserver/login"
        service_url = "https://jw.xmu.edu.cn/login?service=https://jw.xmu.edu.cn/new/index.html"
        
        try:
            resp = self._request("GET", 
                                 login_url,
                                 params={"service": service_url})
            
            execution = re.search(r'name="execution" value="([^"]+)"', resp.text).group(1)
            salt = re.search(r'id="pwdEncryptSalt"\s+value="([^"]+)"', resp.text).group(1)

            ctx = self._get_encrypt_context()
            encrypted_pwd = ctx.call("encryptPassword", password, salt)

            payload = {
                'username': username,
                'password': encrypted_pwd,
                'userPassword': '',
                '_eventId': 'submit',
                'cllt': 'userNameLogin',
                'dllt': 'generalLogin',
                'execution': execution
            }
            
            login_resp = self._request("POST", 
                                       login_url, 
                                       max_retries=1,   # ! 登录请求不重试
                                       params={'service': service_url},
                                       data=payload, 
                                       allow_redirects=True)

            # print(login_resp.url)
            # with open("login_response_fault.html", "w", encoding="utf-8") as f:
            #     f.write(login_resp.text)
            # print("登录响应已保存到 login_response.html，按回车继续...")
            # input()
            
            if self.is_logged_in():
                return True, "登录成功"
            else:
                return False, "登录失败"

        except requests.RequestException as e:
            if isinstance(e, requests.HTTPError) and e.response.status_code == 401:
                return False, "账号或密码错误"
            return False, f"网络请求发生错误: {str(e)}"
        except AttributeError:
            return False, "解析页面参数失败，学校可能更新了登录页"
        except Exception as e:
            logger.exception("发生未知错误")
            return False, f"脚本运行出错: {str(e)}"
        
    def is_logged_in(self) -> bool:
        try:
            resp = self._request("GET",
                                 "https://jw.xmu.edu.cn/jsonp/userDesktopInfo.json")
            data = resp.json()
            # with open("user_status.json", "w", encoding="utf-8") as f:
            #     f.write(resp.text)
            if data.get('hasLogin') is True:
                logger.info(f"Session 有效，已登录用户: {data.get('userName', 'Unknown')}")
                return True
        except Exception as e:
            logger.error(f"检查登录状态时发生错误: {str(e)}")
        
        return False

if __name__ == "__main__":
    client = JWClient(request_interval=request_interval)
    success, message = client.login(username, password)
    if success:
        logger.info("登录成功！")
    else:
        logger.error(f"登录失败: {message}")
    
    if client.is_logged_in():
        logger.info("当前处于登录状态。")
    else:
        logger.info("当前未登录。")