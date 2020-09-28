import re
import os
import json

import requests

"""
获取详细教程、获取代码帮助、提出意见建议
关注微信公众号「裸睡的猪」与猪哥联系

@Author  :   猪哥,
@Version :   2.0"
https://blog.csdn.net/u014044812/article/details/99584382
"""

s = requests.Session()
# cookies序列化文件
COOKIES_FILE_PATH = 'taobao_login_cookies.txt'


class UsernameLogin:

    def __init__(self, loginId, umidToken, ua, password2, _csrf_token=''):
        """
        账号登录对象
        :param loginId: 用户名
        :param umidToken: 新版登录新增参数
        :param ua: 淘宝的ua参数
        :param password2: 加密后的密码
        """
        # 检测是否需要验证码的URL
        self.user_check_url = 'https://login.taobao.com/newlogin/account/check.do?appName=taobao&fromSite=0'
        # 验证淘宝用户名密码URL
        self.verify_password_url = "https://login.taobao.com/newlogin/login.do?appName=taobao&fromSite=0"
        # 访问st码URL
        self.vst_url = 'https://login.taobao.com/member/vst.htm?st={}'
        # 淘宝个人 主页
        self.my_taobao_url = 'http://i.taobao.com/my_taobao.htm'

        # 淘宝用户名
        self.loginId = loginId
        # 淘宝用户名
        self.umidToken = umidToken
        # 淘宝关键参数，包含用户浏览器等一些信息，很多地方会使用，从浏览器或抓包工具中复制，可重复使用
        self.ua = ua
        # 加密后的密码，从浏览器或抓包工具中复制，可重复使用
        self.password2 = password2
        # # token
        # self._csrf_token = _csrf_token

        # 请求超时时间
        self.timeout = 3

    def _user_check(self):
        """
        检测账号是否需要验证码
        :return:
        """
        data = {
            'loginId': self.loginId,
            'ua': self.ua,
        }
        try:
            response = s.post(self.user_check_url, data=data, timeout=self.timeout)
            response.raise_for_status()
        except Exception as e:
            print('检测是否需要验证码请求失败，原因：')
            raise e
        check_resp_data = response.json()['content']['data']
        print("检测账号是否需要验证码, ", response.json())
        needcode = False
        # 判断是否需要滑块验证，一般短时间密码错误多次可能出现
        if 'isCheckCodeShowed' in check_resp_data:
            needcode = True
        print('是否需要滑块验证：{}'.format(needcode))
        return needcode

    def _get_umidToken(self):
        """
        获取umidToken参数
        :return:
        """
        response = s.get('https://login.taobao.com/member/login.jhtml')
        st_match = re.search(r'"umidToken":"(.*?)"', response.text)
        print(st_match.group(1))
        return st_match.group(1)

    @property
    def _verify_password(self):
        """
        验证用户名密码，并获取st码申请URL
        :return: 验证成功返回st码申请地址
        """
        verify_password_headers = {
            'Origin': 'https://login.taobao.com',
            'content-type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://login.taobao.com/member/login.jhtml?spm=a21bo.2017.754894437.1.5af911d9HjW9WC&f=top&redirectURL=https%3A%2F%2Fwww.taobao.com%2F',
        }
        # 验证用户名密码参数
        verify_password_data = {
            'ua': self.ua,
            'loginId': self.loginId,
            'password2': self.password2,
            'umidToken': self.umidToken,
            # '_csrf_token': self._csrf_token,
            'appEntrance': 'taobao_pc',
            'isMobile': 'false',
            'returnUrl': 'https://www.taobao.com/',
            'navPlatform': 'MacIntel',
        }
        try:
            response = s.post(self.verify_password_url, headers=verify_password_headers, data=verify_password_data,
                              timeout=self.timeout)
            response.raise_for_status()
            # 从返回的页面中提取申请st码地址
        except Exception as e:
            print('验证用户名和密码请求失败，原因：')
            raise e
        print('-'*50)
        print("登录部分-验证用户名密码，并获取st码申请URL")
        print(response.text)
        print('-' * 50)
        # 提取申请st码url
        # 登录失败会报错
        apply_st_url_match = response.json()['content']['data']['asyncUrls'][0]
        # 存在则返回
        if apply_st_url_match:
            print('验证用户名密码成功，st码申请地址：{}'.format(apply_st_url_match))
            return apply_st_url_match
        else:
            raise RuntimeError('用户名密码验证失败！response：{}'.format(response.text))

    def _apply_st(self):
        """
        申请st码
        :return: st码
        """
        apply_st_url = self._verify_password
        try:
            response = s.get(apply_st_url)
            response.raise_for_status()
        except Exception as e:
            print('申请st码请求失败，原因：')
            raise e
        print("申请st码: " , response.text)
        st_match = re.search(r'"data":{"st":"(.*?)"}', response.text)
        if st_match:
            print('获取st码成功，st码：{}'.format(st_match.group(1)))
            return st_match.group(1)
        else:
            raise RuntimeError('获取st码失败！response：{}'.format(response.text))


    def login(self):
        """
        使用st码登录
        :return:
        """
        # 加载cookies文件
        if self._load_cookies():
            return True
        # 判断是否需要滑块验证
        self._user_check()
        st = self._apply_st()
        headers = {
            'Host': 'login.taobao.com',
            'Connection': 'Keep-Alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        try:
            response = s.get(self.vst_url.format(st), headers=headers)
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


if __name__ == '__main__':
    # 说明：loginId、umidToken、ua、password2这4个参数都是从浏览器登录页面复制过来的。
    # 如何复制4个参数：
    # # 1、浏览器打开：https://login.taobao.com/member/login.jhtml
    # # 2、F12打开调试窗口，左边有个Preserve log，勾选上，这样页面跳转请求记录不会丢失
    # # 3、输入用户名密码登录，然后找到请求：newlogin/login.do 这个是登录请求
    # # 4、复制上面的4个参数到下面，基本就可以运行了
    # # 5、如果运行报错可以微信私聊猪哥，没加猪哥微信的可以关注猪哥微信公众号[裸睡的猪]，回复：加群

    # 淘宝用户名：手机 用户名 都可以
    loginId = '18306420050'
    # 改版后增加的参数，后面考虑解密这个参数
    umidToken = '59789165bcb9cd1f1757ce5af0534ae132f456a4',
    # 淘宝重要参数，从浏览器或抓包工具中复制，可重复使用
    ua = '125#c6ocaGNCcWQ7DtBm8NbhxPdSuDf2r14YEXzdh0wkDDIBz2r7CrwmPJx7WbWIcL8ykZrfOUWm2quLguQuqPcF6bDUUEYZOdY/yqu3HvJnlaB+SI37hrWnoptjuaun6py8mzecxk41m1T/KsRmickoBSG9cCIE2MNMFf9eG11aE0UU85zocqAGwCnTdgWcnvrke83H/Bpi+F3dvlQ0W0kxO5N/6jPib3tRqx6F0PiNcMdWGqi6DrtNmJSqHBqQOveorUcikuYW8d4Li0WqreVP4qext1eFqg/f6yoGM0V7DPK2qoHftbInsXM7E6hRGlDbccscKJsScUHUcNwi86M9FYnDfJomahDw9cs4/GitcbEgfJ3N/l2Si7PSf9hmfiChSasSKwEcxgnoj3ifJmwTBW/BHz/57yBE/kSVbf73kgTDbNHVQ/ORxkc8LXBgUSbiFo8YuqGORQ8RqcRci8PsItyfwXj4MSaBXefxytV4m5TiEupFUFNckF4RKxh4UT5qKudLPOLOM4OqwaNypu0eBKQLU0m3v5h8LUovGgrvyL4SXbubmPq9ohlBeNOkFCb61e0pl2XIMG+7nDkN6qbfuob5mV+9RnOgt3l425gZO5LeJJiJY7rPClP9S7gkUejBfU/mzquoJowrX6nK9vND9oBI+Zap1omos7ukfOPB4404DcK0XzIRLtLIWKqB45zoajalEEz31UXvYuiHabDDXus6gf+JJ3kcYr+z8HJAQtA7fO8iFiE+jD71zWPdqn1r9vuDXqD19YlKc5h0PbRvdUjHwwLs8bKuPEmdgjaY7Ga5UJbu5QIVkeN3/z2xLybeemf0VpkbJmU1DlBA/wlqvyieBH+ee7VH1rimqpda40fc6VpdNgCYhIVxhB9VYbn1mpYHdaMpBrdcndGbixHJL3Q2RUdEr/G7GaQdORbs1Zo90MMwo3dZfb7Yew/2ITLD6tlczi9RlUns6SH2swGIC6A1iLhArfYXbCkzQ0dry5/lW4LPXrQGFaQilKvU0W68MH+EjQlVw969kyxi1M4TjAP6PXEQnznTYkQEZFmiCSk4mgFncJP='
    # 加密后的密码，从浏览器或抓包工具中复制，可重复使用
    password2 = '5490e3cfc3b4c5d5f3450ec44445eecd46530e858773ad50f2e4573cbc8392abc96eaa9e4e3d2d5e5e571171db6bbbcc4f200eb433495e19cbf96ff85cd8a0687ac8e8757aa72487e6ec7790a40962f34a56ae72ff5b275965bfeb972fb9176cccfd3d09fea62c36c785e4dcd115d2e344636ca33935a2f2d199a43f019dd566'
    # _csrf_token = 'CeqvusPtCosV8mslb9O4s7'
    ul = UsernameLogin(loginId, umidToken, ua, password2)
    ul.login()
    ul.get_taobao_nick_name()
