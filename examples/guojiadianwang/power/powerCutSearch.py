from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from collections import defaultdict
from logCls import Logger
import datetime
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests
import json
from lxml import etree
import re

cityList = ["乌鲁木齐供电公司", "国网昌吉供电公司", "国网吐鲁番供电公司", "国网新疆电力公司奎屯...", "国网博尔塔拉供电公司",
                "国网哈密供电公司", "国网新疆塔城供电有限...", "国网新疆阿勒泰供电有...", "国网新疆电力公司伊犁...",
                "国网新疆巴州供电有限...", "国网和田供电公司", "国网新疆阿克苏供电有...", "国网新疆疆南供电有限..."]

class infoSearch:

    def __init__(self):
        # 设置初始化信息（城市名称，搜索时间范围）
        self.startTime = datetime.datetime.now().date()
        self.endTime = self.startTime + datetime.timedelta(days=2)
        self.mainpage_url = 'http://www.95598.cn/95598/outageNotice/queryOutageNoticeListInit'
        self.sendMessageData = []
        self.logger = Logger("www.95598.cn/95598")
        # 加载json文件倍用
        with open("cityInfo.json", "r", encoding="utf8")as f1, open("dingdingRobotInfo.json", "r",
                                                                    encoding="utf8")as f2:
            self.cityInfo = json.loads(f1.read())
            self.dingdingInfo = json.loads(f2.read())
        # 创建driver
        self.__create_driver()
        self.wait = WebDriverWait(self.driver, 20)

    def __create_driver(self):
        # 创建driver
        options = webdriver.FirefoxOptions()
        options.add_argument(
            'Accept="text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"')
        options.add_argument('Accept-Encoding="gzip, deflate"')
        options.add_argument('Accept-Language="zh-CN,zh-TW;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6"')
        options.add_argument('Connection="keep-alive"')
        options.add_argument('Content-Type="application/x-www-form-urlencoded"')
        options.add_argument('Upgrade-Insecure-Requests="1"')
        options.add_argument(
            'User-Agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0"')
        options.add_argument('-headless')
        driver = webdriver.Firefox(firefox_options=options)
        driver.set_page_load_timeout(60)
        driver.set_script_timeout(10)
        self.driver = driver

    def __quit_driver(self):
        # 推出driver
        if self.driver:
            self.driver.quit()

    def getHtml(self, cityName):
        # 进行信息搜索
        # step 1 使用driver打开对应url
        self.driver.get(self.mainpage_url)
        self.driver.maximize_window()
        htmlData = []
        # 点掉弹出的对话框
        xubox_button = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'span.xubox_botton a.xubox_botton1')))
        if xubox_button:
            xubox_button.click()

        # step 2 选择地区
        add_select_1 = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#orgList__jQSelect0')))
        add_select_1.click()

        addOne = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[@id='orgList__jQSelect0']/div[@class='dropselectbox']/ul/li[contains(text(),'新疆区电力公司')]")))
        addOne.click()

        xubox_button = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'span.xubox_botton a.xubox_botton1')))
        if xubox_button:
            xubox_button.click()

        add_select_2 = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#orgListNext__jQSelect1')))
        add_select_2.click()

        addTwo = self.wait.until(EC.element_to_be_clickable((By.XPATH,
                                                             "//*[@id='orgListNext__jQSelect1']/div[@class='dropselectbox']/ul/li[contains(text(),'{}')]".format(
                                                                 cityName))))
        addTwo.click()

        # step 3 设置时间范围
        xubox_button = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'span.xubox_botton a.xubox_botton1')))
        if xubox_button:
            xubox_button.click()

        startDateInput = self.wait.until(EC.element_to_be_clickable((By.ID, 'staTime')))
        endDateInput = self.wait.until(EC.element_to_be_clickable((By.ID, 'endTime')))

        js = '''var element = document.querySelectorAll("input[readonly='readonly']");
        for(var i = 0;i < element.length; i++)
        {
        element[i].readOnly = false;
        }'''
        self.driver.execute_script(js)
        startDateInput.send_keys(str(self.startTime))
        time.sleep(1)
        endDateInput.send_keys(str(self.endTime))
        time.sleep(1)
        submitButton = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.submitBtn')))

        # step 4 点击查询 进行搜索
        submitButton.click()

        # 通过页面时间输入框能click判断页面加载完成
        self.wait.until(EC.element_to_be_clickable((By.ID, 'staTime')))

        time.sleep(3)
        # step 5滑倒浏览器下方
        downPage = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "wx_tip")))
        self.driver.execute_script('arguments[0].scrollIntoView(true);', downPage)
        # step 6 存储html
        html_text = self.wait.until(EC.presence_of_element_located((By.ID, "noticelist"))).get_attribute("innerHTML")

        if html_text and "没有找到符合条件的信息" not in html_text:
            htmlData.append(html_text)

        else:
            return
        # step 7 判断是否有下一页,如果有click 继续抓取
        print(self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li.inline_block_fix.next"))).get_attribute("class"))

        if "no_page" in self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.inline_block_fix.next"))).get_attribute("class"):
            nextPageButton = False
        else:
            nextPageButton = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.inline_block_fix.next")))


        while nextPageButton:

            self.logger.get_log().debug("正在爬取下一页...")
            nextPageButton.click()

            # 通过页面时间输入框能click判断页面加载完成
            self.wait.until(EC.element_to_be_clickable((By.ID, 'staTime')))

            time.sleep(10)

            html_text = self.wait.until(EC.presence_of_element_located((By.ID, "noticelist"))).get_attribute(
                "innerHTML")
            if html_text:
                htmlData.append(html_text)

            downPage = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "wx_tip")))

            self.driver.execute_script('arguments[0].scrollIntoView(true);', downPage)

            if "no_page" in self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "li.inline_block_fix.next"))).get_attribute(
                "class"):
                nextPageButton = False
            else:
                nextPageButton = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "li.inline_block_fix.next")))

            time.sleep(2)
        time.sleep(2)

        if htmlData:
            return set(htmlData)
        else:
            return

    def responseParse(self, htmlData):
        # html解析
        sendMessageByTown = defaultdict(list)
        sendMessageByTown.clear()
        dateList = []

        if not htmlData:
            return

        for html in htmlData:
            demo = etree.HTML(html)
            powerCutTitle = demo.xpath("//div[@class='xinxi']/h4/text()")
            powerCutTime = demo.xpath("//div[@class='xinxi']/p[@class='p1']/i/text()")
            powerCutArea = demo.xpath("//div[@class='xinxi']/p[@class='p2']/text()")
            powerCutLine = demo.xpath("//div[@class='xinxi']/p[@class='p3']/text()")

            for index in range(len(powerCutTitle)):
                townName = re.findall(r"【(.*?)】", powerCutArea[index].replace("[", "【").replace("]", "】"))
                if townName:
                    townName = townName[-1]
                else:
                    townName = ""
                dateList.append(powerCutTime[index].split("—"))
                text = '- {}\n- 【停电时间】：{}\n- 【停电范围】：{}\n- 【停电线路】：{}\n---'.format(
                    powerCutTitle[index],
                    powerCutTime[index],
                    powerCutArea[index],
                    powerCutLine[index])

                if powerCutTime[index].split("—")[0] > str(self.startTime):
                    msg = {
                        "text": text,
                        "startDate": powerCutTime[index].split("—")[0]
                    }

                    sendMessageByTown[townName].append(msg)

        sendMessageByTown = {k: sorted(v, key=lambda x: x["startDate"]) for k, v in sendMessageByTown.items()}
        sendMessageByTown = {k: f"\n".join([i["text"] for i in v]) for k, v in sendMessageByTown.items()}

        return sendMessageByTown

    def makeMessage(self, sendMessageDict, cityName):
        message_list = []
        for townName, message in sendMessageDict.items():
            ddInfo = self.cityInfo.get(cityName).get(townName)
            self.logger.get_log().debug("\n查询{}的信息：{}".format(townName, ddInfo))
            if ddInfo:
                mobiles = ddInfo.get("mobiles", [])
                secret = ddInfo.get("sign")
                webHook = ddInfo.get("webhook")
            else:
                mobiles = []
                secret = self.dingdingInfo.get(cityName)[0]
                webHook = self.dingdingInfo.get(cityName)[1]

            if mobiles:
                message = f"##{townName}停电信息公告##\n" + "\n@{}\n".format("@".join(mobiles)) + message
            else:
                message = f"##{townName}停电信息公告##\n" + message
            msg = (secret, webHook, mobiles, townName, message)
            message_list.append(msg)

        return message_list

    def sendMessage(self, messageList):
        for msg in messageList:
            secret = msg[0]
            webHook = msg[1]
            mobiles = msg[2]
            townName = msg[3]
            sendText = msg[4]
            # 使用钉钉机器人发送定制消息
            timestamp = str(round(time.time() * 1000))
            secret_enc = secret.encode('utf-8')
            string_to_sign = '{}\n{}'.format(timestamp, secret)
            string_to_sign_enc = string_to_sign.encode('utf-8')
            hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            webhook = "{}&timestamp={}&sign={}".format(webHook, timestamp, sign)
            headers = {"Content-Type": "application/json",
                       "Charset": "UTF-8"}

            # 消息类型和数据格式参照钉钉开发文档
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": "{}停电信息公告".format(townName),
                    "text": sendText,
                },
                "at": {
                    "atMobiles": mobiles,
                    "isAtAll": "false"
                }
            }
            self.logger.get_log().debug("\n" + sendText)

            # with open(f"{str(datetime.datetime.now().date())}.txt", "a+", encoding="utf-8")as f:
            #     f.write("\n" + sendText)

            r = requests.post(webhook, data=json.dumps(data), headers=headers)
            time.sleep(1)
            self.logger.get_log().debug(r.text)


    def searchByCtiyName(self, cityName):
        # 主函数
        self.logger.get_log().debug("正在查询【{}】停电信息...".format(cityName))
        try:
            htmlData = self.getHtml(cityName)
            if htmlData:
                sendMessageDict = self.responseParse(htmlData)
                sendMessageList = self.makeMessage(sendMessageDict, cityName)
                if sendMessageDict:
                    self.sendMessage(sendMessageList)
                    self.logger.get_log().debug("\n" + "-" * 100)
                else:
                    self.logger.get_log().debug("【{}】没有停电信息...".format(cityName))
        except Exception as e:
            self.logger.get_log().debug(e.args)
            self.logger.get_log().debug("正在重试...")
            self.searchByCtiyName(cityName)

    def run(self):
        for cityName in cityList:
            self.searchByCtiyName(cityName)

        self.__quit_driver()

if __name__ == '__main__':
    ooo1 = infoSearch()
    ooo1.run()

