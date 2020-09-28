import requests
from utils import loginFile, dataAnalysis
import os
import datetime
from dateutil.relativedelta import relativedelta
import json
from utils.logCls import Logger

dirpath = os.path.dirname(__file__)

cookieFile = f"{dirpath}/utils/cookies.txt"
dataFile = f"{dirpath}/datas"


class DevopsProject:

    def __init__(self, logFileName):
        # 初始化搜索起始与截止时间
        self.endDate = datetime.datetime.today().date()
        self.startDate = self.endDate - relativedelta(months=+1)
        # log日志
        self.logger = Logger("[告警信息通报({}-{})]".format(self.startDate, self.endDate), logFileName)

    def _load_cookies(self):
        print("----------_load_cookies----------")
        # 加载cookie
        if not os.path.exists(cookieFile):
            return False
        # 3、判断cookies是否过期
        try:
            with open(cookieFile, "r")as f:
                cookies = f.read()
            if self.login_check(cookies):
                return cookies
            else:
                return

        except Exception as e:
            print(e.args)
            os.remove(cookieFile)
            self.logger.get_log().debug("[cookies过期]")
            return False


    def login_check(self, cookies):
        # cookie验证是否有效
        self.logger.get_log().debug("[正在验证cookie]")
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh-TW;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Cookie': cookies,
            'Host': 'xt.devops123.net',
            'Referer': 'http://xt.devops123.net/Welcome/login/',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
        }
        checkUrl = "http://xt.devops123.net/portal/substation_list/991"
        response = requests.get(checkUrl, headers=headers)
        if response.status_code == 200:
            if "管理面板" in response.text:
                self.logger.get_log().debug("[加载cookie成功]")
                return True
            else:
                self.logger.get_log().debug("[加载失败, 正在进行登录]")
                return False

        raise response.raise_for_status()

    def login(self):
        # 登录
        cookies = self._load_cookies()
        if cookies:
            return cookies

        cookies = loginFile.loginDevops().login()

        return cookies

    def getReportData(self, cookies):
        self.logger.get_log().debug("[正在搜索告警信息]")
        self.searchTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 搜索告警信息
        downloadUrl = "http://xt.devops123.net/alarm?selCity=&selCounty=0&selSubstation=&selRoom=&level=1&selDevModel=&selStatus%5B%5D=unresolved&reportDate={}%E8%87%B3{}&selSignalName=&substationType%5B%5D=A%E7%BA%A7%E5%B1%80%E7%AB%99&substationType%5B%5D=B%E7%BA%A7%E5%B1%80%E7%AB%99&substationType%5B%5D=C%E7%BA%A7%E5%B1%80%E7%AB%99&substationType%5B%5D=D%E7%BA%A7%E5%B1%80%E7%AB%99&substationType%5B%5D=D1%E7%BA%A7%E5%B1%80%E7%AB%99&word=&export=exporttoexcel"
        headers = {
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Referer': 'http://xt.devops123.net/alarm?level=1',
            'Cookie': cookies,
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh-TW;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6'
        }

        response = requests.get(downloadUrl.format(str(self.startDate), str(self.endDate)), headers=headers)
        return response.text

    def getDingDingInfo(self, cityName):
        # 加载钉钉机器人信息
        with open("utils/dingdingRobotInfo.json", "r", encoding="utf-8")as f:
            robotInfo = json.loads(f.read())
        if cityName in list(robotInfo.keys()):
            SECRET = robotInfo.get(cityName)[0]
            WEBHOOK = robotInfo.get(cityName)[1]
            return SECRET, WEBHOOK
        else:
            self.logger.get_log().debug("[没有该{}对应的钉钉信息，请检查dingdingRobotInfo.json文件]".format(cityName))
            return

    def detail_data(self, dataList, monitorInfo, warn5=False, byhour=False):
        if warn5:
            for data in dataList:
                k, group = data
                SECRET, WEBHOOK = self.getDingDingInfo(k)
                htmlPath = dataAnalysis.data2html(k, group, dataFile, k2="超过5天告警信息汇总")
                imgFile = dataAnalysis.html2image(htmlPath)
                imgUrl = dataAnalysis.img2url(imgFile)
                sendTitle = f"{k}-{'超过5天告警信息汇总'}\n\n- 数据提取时间:{self.searchTime}\n- 上报时间段:\t{self.startDate}至{self.endDate} \n"
                sendText = sendTitle + "\n".join(
                    [f"- {k}:\t{v}条" for k, v in group.groupby("信号名称")["信号名称"].count().sort_values(ascending=False).to_dict().items()])

                yield k, SECRET, WEBHOOK, imgUrl, sendText
        else:
            for data in dataList:
                k, group = data
                if byhour:
                    group = group.loc[group["信号名称"].isin(monitorInfo)]
                SECRET, WEBHOOK = self.getDingDingInfo(k)
                htmlPath = dataAnalysis.data2html(k, group, dataFile)
                imgFile = dataAnalysis.html2image(htmlPath)
                imgUrl = dataAnalysis.img2url(imgFile)
                sendText = "\n".join([f"- {k}:\t{v}条" for k, v in group.groupby("区域")["区域"].count().to_dict().items()])
                yield k, SECRET, WEBHOOK, imgUrl, sendText

    def reportTotal(self, totalInfo, monitorInfo):
        self.logger.get_log().debug("正在汇总信息...")
        cityNames = ["乌鲁木齐", "昌吉", "吐鲁番", "奎屯", "博州", "哈密", "塔城", "阿勒泰", "伊犁", "巴州",
                     "和田", "阿克苏", "石河子", "喀什", "克州", "克拉玛依"]
        totalSendTextByCity = {}
        summaryInfo = dataAnalysis.dataSummary(totalInfo)
        for city in cityNames:
            summaryText = "\n".join([f"- {k} : {v}条" for k, v in summaryInfo.get(city, {}).items() if k in monitorInfo])
            if summaryText:
                totalSendText = f"{self.startDate}至{self.endDate}\n- #告警消息汇总#\n- 数据提取时间:{self.searchTime}\n- #按照信号名称汇总如下#\n" + summaryText
            else:
                totalSendText = f"{self.startDate}至{self.endDate}\n- 数据提取时间:{self.searchTime}\n" + "无告警信息."

            totalSendTextByCity[city] = totalSendText

        return totalSendTextByCity


    def monitorByHour(self):
        try:
            monitorInfo = ["通信状态", "烟感", "温度", "交流输入停电警告", "交流输入停电告警", "蓄电池组总电压过低", "水浸", "电池熔丝故障告警", "蓄电池总电压过高"]
            self.logger.get_log().debug("[正在登录]")
            new_cookie = self.login()
            # 获取excel的xml
            self.logger.get_log().debug("[进入【温度】【交流输入停电告警】【蓄电池组总电压过低】监控...(监控频率：每小时一次)]")
            xmlData = self.getReportData(new_cookie)
            # 分析xml
            if dataAnalysis.parseData(xmlData, dataFile):
                totalInfo, warn5days, dataList = dataAnalysis.parseData(xmlData, dataFile, byhour=True)
                totalSendTextByCity = self.reportTotal(totalInfo, monitorInfo)
                self.logger.get_log().debug("[发送告警信息]")
                for k, SECRET, WEBHOOK, imgUrl, sendText in self.detail_data(dataList, monitorInfo, byhour=True):
                    totalSendText = totalSendTextByCity.get(k)
                    if "无告警信息" in totalSendText:
                        dataAnalysis.sendMessage(SECRET, WEBHOOK, totalSendText, imgUrl="")
                        self.logger.get_log().debug(totalSendText)
                    else:
                        sendTextTotal = f"{totalSendText}\n{'- #按照县汇总如下#'}\n{sendText}"
                        dataAnalysis.sendMessage(SECRET, WEBHOOK, sendTextTotal, imgUrl)
                        self.logger.get_log().debug(sendTextTotal)

            self.logger.get_log().debug("[告警信息发送结束]")
            dataAnalysis.clearDir(dataFile)

        except Exception as e:
            self.logger.get_log().debug(e.args)

    def monitorByDay(self):
        try:
            self.logger.get_log().debug("[进入【通信状态】【烟感】【水浸】【电池熔丝故障告警】【蓄电池总电压过高】【手动控制状态】【启动电池电压低】监控...(监控频率：每天一次)]")
            monitorInfo = ["通信状态", "烟感", "水浸", "电池熔丝故障告警", "蓄电池总电压过高", "手动控制状态", "启动电池电压低", "交流输入停电警告", "交流输入停电告警", "温度",
                           "蓄电池组总电压过低"]
            new_cookie = self.login()
            # 获取excel的xml
            xmlData = self.getReportData(new_cookie)
            # 分析xml
            if dataAnalysis.parseData(xmlData, dataFile):
                totalInfo, warn5days, dataList = dataAnalysis.parseData(xmlData, dataFile)
                totalSendTextByCity = self.reportTotal(totalInfo, monitorInfo)

                self.logger.get_log().debug("[汇总告警时间超过5天的信息]")
                for k, SECRET, WEBHOOK, imgUrl, sendText in self.detail_data(warn5days, monitorInfo, warn5=True):
                    self.logger.get_log().debug(sendText)
                    dataAnalysis.sendMessage(SECRET, WEBHOOK, sendText, imgUrl)

                self.logger.get_log().debug("[汇总告警信息]")
                for k1, SECRET, WEBHOOK, imgUrl, sendText in self.detail_data(dataList, monitorInfo):
                    totalSendText = totalSendTextByCity.get(k1)
                    if "无告警信息" in totalSendText:
                        dataAnalysis.sendMessage(SECRET, WEBHOOK, totalSendText, imgUrl="")
                        self.logger.get_log().debug(totalSendText)
                    else:
                        sendTextTotal = f"{totalSendText}\n{'- #按照县汇总如下#'}\n{sendText}"
                        self.logger.get_log().debug(sendTextTotal)
                        dataAnalysis.sendMessage(SECRET, WEBHOOK, sendTextTotal, imgUrl)

                self.logger.get_log().debug("告警信息发送结束")
        except Exception as e:
            self.logger.get_log().debug(e.args)

    def main(self):
        # 主函数
        self.monitorByDay()
        # self.monitorByHour()


if __name__ == '__main__':
    demo = DevopsProject("test")
    demo.main()
