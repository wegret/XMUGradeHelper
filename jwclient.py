'''
Author: wlaten
Date: 2026-01-10 15:24:29
LastEditTime: 2026-01-12 16:31:16
Discription: file content
'''
import os, dotenv, time
import json
import requests
import logging
import execjs
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

try:
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    pass

os.makedirs("cache", exist_ok=True)

class JWClient:
    def __init__(self, request_interval: int = 1):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
        })  # todo 随机UA
        # self.js_path = "cache/encrypt.js"
        
        self.last_request_time = 0
        self.request_interval = request_interval
    
    def _request(self,
                 method: str,
                 url: str,
                 max_retries: int = 3,
                 headers: dict = None,
                 **kwargs) -> requests.Response:
        """
        带重试机制的底层请求封装
        :return: 成功的 Response 对象
        :raise: 超过重试次数后抛出异常，由上层捕获
        """
        kwargs.setdefault('timeout', 10)
        last_exception = None
        
        if headers:
            if 'headers' not in kwargs:
                kwargs['headers'] = {}
            kwargs['headers'].update(headers)
        
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
    
    def get_grade_report(self):
        """
        获取成绩报告
        
        返回：
        {
            "total_credits": float,    # 总学分，返回这个是为了快速比较成绩是否有更新
            "courses": [
                {
                    "course_name": str,
                    "course_credits": float,
                    "course_grade": str
                },
                ...
            ]
        }
        
        # todo 暂时还没有错误处理逻辑
        """
        
        logger.info("获取应用入口...")
        app_resp = self._request("GET",
                                "https://jw.xmu.edu.cn/appShow",
                                params={"appId": "6925823576580372"},
                                allow_redirects=True)
        referer = app_resp.url  # 获取重定向后的 URL 作为 Referer
        common_headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://jw.xmu.edu.cn",
            "Referer": referer
        }
        
        logger.info("获取证明列表...")
        cert_list_resp = self._request("POST",
                                       "https://jw.xmu.edu.cn/jwapp/sys/zmsqxmu/modules/xszmsq/dsqzmcx.do",
                                       headers=common_headers,
                                       data={
                                           "*order": "+WID",
                                           "pageSize": "200",
                                           "pageNumber": "1"
                                       })
        cert_data = cert_list_resp.json()
        
        certificates = cert_data.get("datas", {}).get("dsqzmcx", {}).get("rows", [])
        wid_cert = None
        name_cert = None
        for cert in certificates:
            name = cert.get("ZMWJMC", "")
            if "本科生主修成绩单" in name and "中文" in name:
                wid_cert = cert.get("WID")
                name_cert = name
                logger.info(f"找到成绩单证明: {name_cert} (WID: {wid_cert})")
                break
        
        if not wid_cert:
            pass
        
        logger.info("查询证明信息...")
        zm_resp = self._request("POST",
                                "https://jw.xmu.edu.cn/jwapp/sys/zmsqxmu/xszmsq/queryZmxx.do",
                                headers=common_headers,
                                data={"wid": wid_cert})
        
        zm_data = zm_resp.json()
        
        # with open("cache/zm.json", "w", encoding="utf-8") as f:
        #     f.write(zm_resp.text)
        # input("成绩单信息已保存到 cache/zm.json，按回车继续...")
        
        if "wid" not in zm_data:
            pass
        
        wid_report = zm_data.get("wid")
        name_report = zm_data.get("mb")
        
        logger.info(f"获取到报表信息 wid: {wid_report}, 报表名: {name_report}")
        
        logger.info("生成成绩报告...")
        
        report_resp = self._request("POST",
                                    "https://jw.xmu.edu.cn/jwapp/sys/frReport2/show.do",
                                    headers=common_headers,
                                    data={
                                        "wid": wid_report,
                                        "reportlet": f"zmsqxmu/{name_report}"
                                    })
        
        # with open("cache/grade_report.html", "w", encoding="utf-8") as f:
        #     f.write(report_resp.text)
        
        session_match = re.search(r"currentSessionID\s*=\s*['\"](\d+)['\"]", 
                                    report_resp.text)
        if not session_match:
            pass
        
        session_id = session_match.group(1)
        logger.info(f"获取到session_id: {session_id}")
        
        page_num = 1
        total_pages = None
        
        total_credits = None    # 不设置成0是因为直接抓成绩单的，不是累加的
        courses = []
        
        while True:
            logger.info(f"正在获取第 {page_num} 页...")
            
            page_resp = self._request("GET",
                                      "https://jw.xmu.edu.cn/jwapp/sys/frReport2/show.do",
                                      params={
                                          "_": str(int(time.time() * 1000)),
                                          "__boxModel__": "true",
                                          "op": "page_content",
                                          "sessionID": session_id,
                                          "pn": page_num})
            
            # with open(f"cache/report_page_{page_num}.html", "w", encoding="utf-8") as f:
            #     f.write(page_resp.text)
            # input(f"当前 {page_num} 页已保存，按回车继续...")
            
            if total_pages is None:
                m = re.search(r"reportTotalPage\s*=\s*([0-9]+)", page_resp.text)
                if m:
                    total_pages = int(m.group(1))
            
            total_credits_match = re.search(r"已获学分：([\d.]+)", page_resp.text)
            if total_credits_match:
                total_credits = float(total_credits_match.group(1))
            
            courses.extend(self._parse_course_page(page_resp.text))
            logger.info(f"解析第 {page_num} 页完成，当前已获取 {len(courses)} 门课程")
            
            page_num += 1
            if total_pages and page_num > total_pages:
                break
            
            if page_num > 10:    # todo 极端情况，防止死循环
                pass
        
        return {
            "total_credits": total_credits,
            "courses": courses
        }
    
    def _parse_course_page(self, html: str) -> list[dict]:
        """
        解析一页课程成绩，返回课程列表
        """
        soup = BeautifulSoup(html, "lxml")
        courses = []
        
        for tr in soup.find_all("tr"):
            style = tr.get("style", "")
            if "display:none" in style:
                continue
            
            cells = {td["id"][0]: td.get_text(strip=True) for td in tr.find_all("td") if td.get("id")}
            
            if cells.get("A") and cells.get("D") and cells.get("E"):
                try:
                    courses.append({
                        "course_name": cells["A"].strip(),
                        "course_credits": float(cells["D"]),
                        "course_grade": cells["E"].strip()  # 这个可能是免修或者合格
                    })
                except ValueError:
                    pass  # 可能是其他内容，不是成绩
            
            if cells.get("F") and cells.get("K") and cells.get("L"):
                try:
                    courses.append({
                        "course_name": cells["F"].strip(),
                        "course_credits": float(cells["K"]),
                        "course_grade": cells["L"].strip()
                    })
                except ValueError:
                    pass
                
        return courses

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    username = os.getenv("XMU_USERNAME")
    password = os.getenv("XMU_PASSWORD")
    request_interval = int(os.getenv("REQUEST_INTERVAL", 0.75))    # 请求间隔，单位秒
    
    client = JWClient(request_interval=request_interval)
    success, message = client.login(username, password)
    if success:
        logger.info("登录成功！")
    else:
        logger.error(f"登录失败: {message}")
    
    report = client.get_grade_report()
    with open("cache/grade_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=4)
    
    # with open("cache/grade_report.json", "r", encoding="utf-8") as f:
    #     report = json.load(f)
    
    print(f"总学分: {report['total_credits']}")
    
    sum = 0
    for course in report['courses']:
        if course['course_grade'] not in ['免修']:
            sum += course['course_credits']
    
    print(f"课程数: {len(report['courses'])}, 学分和: {sum}")   # ? 这里不一样是教务系统固有问题，我测试的时候数过了，最后统计出来的就是不一样