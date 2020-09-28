import re
import os
import json
import requests
import execjs
from lxml import etree
from utils import chaojiying
from PIL import Image
# cookies序列化文件
COOKIES_FILE_PATH = 'login_cookies.txt'


class PdwebLogin:

    def __init__(self, loginId, password):
        self.sess = requests.Session()

        # 用户名
        self.loginId = loginId
        self.password = password
        # homepage:登录界面
        self.homePage = "http://135.224.81.37:18006/pdweb/pwb/bdf/jsf/login.xhtml"
        # 登录链接
        self.loginUrl = "http://135.224.81.37:18006/pdweb/pwb/bdf/jsf/login.xhtml"
        # 请求超时时间
        self.timeout = 3
        # 加载js文件
        with open("jscode.js", "r", encoding="utf8") as f:
            self.jscode = f.read()
            self.ctx = execjs.compile(self.jscode)

        # 超级鹰
        self.cjy_usr = "peng4150"
        self.cjy_pwd = "pengchao123"
        self._verify = chaojiying.Chaojiying_Client(self.cjy_usr, self.cjy_pwd, 4004)

    def encode(self, value):

        return self.ctx.call("encode", value)

    def get_uuid(self):
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
        }
        response = self.sess.get(self.homePage, headers=headers)
        element = etree.HTML(response.text)
        uuid = element.xpath("//*[@id='uuid']/@value")
        return uuid


    def get_captcha(self):
        captchaUrl = "http://135.224.81.37:18006/pdweb/servlet/ValidateCodeServlet"
        headers = {
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'http://135.224.81.37:18006/pdweb/pwb/bdf/jsf/login.xhtml',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
        }
        response = self.sess.get(captchaUrl, headers=headers)
        if response.status_code==200:
            with open("utils/captcha.jpg", "wb")as f:
                f.write(response.content)

    def verify_captcha(self, captchaImg):
        image = Image.open(captchaImg)
        result = json.loads(self._verify.PostPic(image, 4004))

        return result.get("pic_str")
        # {'err_no': 0, 'err_str': 'OK', 'pic_id': '9111116351507400589', 'pic_str': '5423', 'md5': '535cf32c961947ac94db594af71af931'}


    def login(self):
        # 加载cookies文件
        if self._load_cookies():
            return True

        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': '135.224.81.37:18006',
            'Origin': 'http://135.224.81.37:18006',
            'Referer': 'http://135.224.81.37:18006/pdweb/pwb/bdf/jsf/login.xhtml',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
        }

        self.sess.get(self.homePage, headers=headers)

        # 登录
        formData = {
            'AJAXREQUEST': '_viewRoot',
            'loginForm': 'loginForm',
            'uuid': 'de6e0d2c-f298-404b-844a-32e7cc397a45',
            'method': 'login',
            'loginForm:loginName': self.encode(self.loginId),
            'loginForm:password': self.encode(self.password),
            'loginForm:validateCode': '0400',
            'loginForm:framePage': '/pwb/main/jsp/main.jsp',
            'loginForm:userId': '',
            'javax.faces.ViewState': 'j_id1',
            'loginForm:btnLogin': 'loginForm:btnLogin'
        }
        response = self.sess.post(self.loginUrl, data={}, headers=headers)

        try:
            response = self.sess.get(self.loginUrl, headers=headers)
            response.raise_for_status()
        except Exception as e:
            print('st码登录请求，原因：')
            raise e
        # 登录成功，提取跳转淘宝用户主页url
        print("录成功，提取跳转淘宝用户主页url", response.text)
        my_taobao_match = re.search(r'top.location.href = "(.*?)"', response.text)
        if my_taobao_match:
            print('登录淘宝成功，跳转链接：{}'.format(my_taobao_match.group(1)))
            self.my_taobao_url = my_taobao_match.group(1)
            self._serialization_cookies()
            return True
        else:
            raise RuntimeError('登录失败！response：{}'.format(response.text))

    def _load_cookies(self):
        # 1、判断cookies序列化文件是否存在
        if not os.path.exists(COOKIES_FILE_PATH):
            return False
        # 2、加载cookies
        s.cookies = self._deserialization_cookies()
        # 3、判断cookies是否过期
        try:
            self.get_taobao_nick_name()
        except Exception as e:
            os.remove(COOKIES_FILE_PATH)
            print('cookies过期，删除cookies文件！')
            return False
        print('加载淘宝cookies登录成功!!!')
        return True

    def _serialization_cookies(self):
        """
        序列化cookies
        :return:
        """
        cookies_dict = requests.utils.dict_from_cookiejar(s.cookies)
        with open(COOKIES_FILE_PATH, 'w+', encoding='utf-8') as file:
            json.dump(cookies_dict, file)
            print('保存cookies文件成功！')

    def _deserialization_cookies(self):
        """
        反序列化cookies
        :return:
        """
        with open(COOKIES_FILE_PATH, 'r+', encoding='utf-8') as file:
            cookies_dict = json.load(file)
            cookies = requests.utils.cookiejar_from_dict(cookies_dict)
            return cookies

    def get_taobao_nick_name(self):
        """
        获取淘宝昵称
        :return: 淘宝昵称
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        try:
            response = s.get(self.my_taobao_url, headers=headers)
            response.raise_for_status()
        except Exception as e:
            print('获取淘宝主页请求失败！原因：')
            raise e
        # 提取淘宝昵称
        print("提取淘宝昵称")
        print(response.text)
        nick_name_match = re.search(r'<input id="mtb-nickname" type="hidden" value="(.*?)"/>', response.text)
        if nick_name_match:
            print('登录淘宝成功，你的用户名是：{}'.format(nick_name_match.group(1)))
            return nick_name_match.group(1)
        else:
            raise RuntimeError('获取淘宝昵称失败！response：{}'.format(response.text))
