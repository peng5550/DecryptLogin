import requests
import json
import re
from utils import chaojiying
import hashlib
import os

dirpath = os.path.dirname(__file__)
loginFileName = r"{}\loginInfo.txt".format(dirpath)


class loginDevops:

    def __init__(self):
        with open(loginFileName, "r")as f:
            self.loginData = json.loads(f.read())
        self.loginID = self.loginData.get("loginId")
        self.passwd = self.loginData.get("password")
        self.cookies = []
        self.cookieFile = f"{dirpath}/cookies.txt"
        # 超级鹰
        self.cjy_usr = "peng5550"
        self.cjy_pwd = "pengchao123"
        self._verify = chaojiying.Chaojiying_Client(self.cjy_usr, self.cjy_pwd, 4004)
        self.sess = requests.Session()
        self.sess.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh-TW;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Host': 'xt.devops123.net',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
        }

    def login(self):
        '''
        登录
        :return: 返回cookies
        '''
        captchaCode = self.captcha_check()
        if not captchaCode:
            print("验证码验证失败，正在进行重新验证....")
            self.login()
        loginUrl = "http://xt.devops123.net/Welcome/login/"
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh-TW;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': "; ".join(self.cookies),
            'Host': 'xt.devops123.net',
            'Origin': 'http://xt.devops123.net',
            'Referer': 'http://xt.devops123.net/Welcome/login/',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
        }
        self.sess.headers = headers
        loginData = {
            "txtUsername": self.loginID,
            "txtCode": captchaCode,
            "cbIsRemember": "true",
            "md5Password": hashlib.md5(self.passwd.encode()).hexdigest(),
            "txtPhoneNumber": "",
            "txtMessageCode": ""
        }
        response = self.sess.post(loginUrl, data=loginData, headers=headers)
        if "管理面板" in response.text:
            print(response.text)
            XJTELEDH_USERNAME = self.sess.cookies.get("XJTELEDH_USERNAME")
            XJTELEDH_HASH = self.sess.cookies.get("XJTELEDH_HASH")
            XT = self.sess.cookies.get("xt-devops123-net-16756-web")
            self.cookies.append("XJTELEDH_USERNAME=" + XJTELEDH_USERNAME)
            self.cookies.append("XJTELEDH_HASH=" + XJTELEDH_HASH)
            self.cookies.append("xt-devops123-net-16756-web=" + XT)
            print("登录成功！")

            with open("cookies.txt", "w+")as f:
                f.write("; ".join(self.cookies))
            return "; ".join(self.cookies)

    def _get_captcha_image(self):
        '''
        获取验证码
        :return:
        '''

        homePage = "http://xt.devops123.net/Welcome/login/"
        response = self.sess.get(homePage)
        PHPSESSID = response.cookies.get("PHPSESSID")
        self.cookies.append("PHPSESSID={}".format(PHPSESSID))

        captcha_url = "http://xt.devops123.net/welcome/get_captcha"
        img_headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh-TW;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6',
            'Connection': 'keep-alive',
            'Content-Length': '0',
            'Cookie': "; ".join(self.cookies),
            'Host': 'xt.devops123.net',
            'Origin': 'http://xt.devops123.net',
            'Referer': 'http://xt.devops123.net/Welcome/login/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        response = self.sess.post(captcha_url, data=json.dumps({}), headers=img_headers)
        self.cookies.append("cap_key=" + response.cookies.get("cap_key"))

        img_url_find = re.findall(r'src="(.*?)"', response.text)
        if img_url_find:
            img_url = "http://xt.devops123.net" + img_url_find[0]
            with open("captcha.jpg", "wb")as f:
                response = self.sess.get(img_url)
                f.write(response.content)

            return True
        return False

    def _verify_captcha(self):
        with open("captcha.jpg", "rb")as f:
            image = f.read()
        result = self._verify.PostPic(image, 4004)
        print(result)
        return result.get("pic_str")

    def captcha_check(self):
        download_captcha = self._get_captcha_image()
        if not download_captcha:
            print("验证码图片下载失败...")
            return

        captchaCode = self._verify_captcha()

        # check_url = "http://xt.devops123.net/welcome/checkcaptcha"
        # headers = {
        #     'Accept': 'application/json, text/javascript, */*; q=0.01',
        #     'Accept-Encoding': 'gzip, deflate',
        #     'Accept-Language': 'zh-CN,zh-TW;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6',
        #     'Connection': 'keep-alive',
        #     'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        #     'Cookie': "; ".join(self.cookies),
        #     'Host': 'xt.devops123.net',
        #     'Origin': 'http://xt.devops123.net',
        #     'Referer': 'http://xt.devops123.net/Welcome/login/',
        #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
        #     'X-Requested-With': 'XMLHttpRequest'
        # }
        # check_data = {"txtCode":captchaCode}
        # response = requests.post(check_url, data=check_data, headers=headers)
        # print(2222222222222, response.text)
        # if "true" in response.text:
        #     print("验证码验证成功...")
        return captchaCode
        # return


if __name__ == '__main__':
    demo = loginDevops()
    demo.login()
