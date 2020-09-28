import base64
import hashlib
import hmac
import json
import urllib.parse
import imgkit
import pandas as pd
from pyquery import PyQuery as pq
import os
import requests
import shutil
import time
import datetime
from qiniu import Auth, put_file, etag, urlsafe_base64_encode
import ssl
ssl._create_default_https_context = ssl._create_unverified_context


monitorInfo = ["通信状态", "烟感", "水浸", "电池熔丝故障告警", "蓄电池总电压过高", "手动控制状态", "交流输入停电警告", "交流输入停电告警", "温度", "蓄电池组总电压过低",
               "启动电池电压低"]


def parseData(xmlText, dataFile, byhour=False):
    '''
    分析excel的xml
    :param xmlText:excel的xml
    :param dataFile: html和图片保存路径 datas文件夹绝对路径
    :return: 按照信号名称区整理的数据信息，汇总
    '''

    dataList = []
    dataList5 = []
    # remove之前的所有文件
    if not os.path.exists(dataFile):
        os.mkdir(dataFile)

    pqxml = pq(xmlText.encode("utf-8"), parser="html").remove("Table Row:nth-child(1)")

    arrayData = []
    for row in pqxml.find("Table Row").items():
        if "总计" not in row:
            rowData = []
            for data in row.find("Data").items():
                rowData.append(data.text())
            arrayData.append(rowData)

    df = pd.DataFrame(arrayData[1:], columns=arrayData[0])
    df["上报时间"] = pd.to_datetime(df["上报时间"])
    df["时间差"] = abs(((df["上报时间"] - pd.datetime.now()) / pd.Timedelta(1, 'D')).fillna(0).astype(int))
    data = df.loc[:, ["分公司", "区域", "局站", "信号名称", "描述", "上报时间", "当前状态", "时间差"]]
    data = data.loc[data["信号名称"].isin(monitorInfo)]
    warn5days = data.loc[data["时间差"] >= 5]
    _warn5days = warn5days.groupby("分公司")
    for k, group in _warn5days:
        group = group.loc[:, ["信号名称", "区域", "局站", "描述", "上报时间"]].sort_values(by="信号名称")
        dataList5.append((k, group))

    _data = data.groupby(["分公司"])

    if not byhour:
        for k, group in _data:
            group = group.loc[:, ["区域", "局站", "描述", "上报时间"]].sort_values(by=["区域", "局站", "上报时间"])
            dataList.append((k, group))
    else:
        for k, group in _data:
            group = group.loc[:, ["信号名称", "区域", "局站", "描述", "上报时间"]].sort_values(by=["信号名称", "上报时间"])
            dataList.append((k, group))

    return data, dataList5, dataList


def dataSummary(data):
    '''
    信息统计
    :param data:
    :return:
    '''
    countBySign = data.groupby(["分公司", "信号名称"])["信号名称"].count()
    cityName = set([i[0] for i in countBySign.index])
    citySummaryData = {k: countBySign[k].sort_values(ascending=False).to_dict() for k in cityName}
    return citySummaryData


def data2html(k1, group, dataFile, k2=False):
    '''
    把分析得到的数据转为html
    :param k1: 县名称
    :param k2: 信号名称
    :param group: parseData分析的的dataList中的数据
    :param dataFile: html和图片保存路径 datas文件夹绝对路径
    :return: 返回html的文件路径信息
    '''
    if k2:
        path = r"{}/{}—{}-{}.html".format(dataFile, k1, k2, int(time.time()))
        title = "{}—{}".format(k1, k2)
    else:
        path = r"{}/{}-{}.html".format(dataFile, k1, int(time.time()))
        title = k1

    data = group.to_html(index=False)
    with open(path, "a+", encoding="utf-8")as f:
        css = '''
    <html>
    <head>
        <meta charset="utf-8">
        <title>告警信息</title>
        <style>
            body {
                font-family: Arial;
                font-size: 14px;
                line-height: 180%;
                padding-top: 20px;
                background: lightgoldenrodyellow;
            }
    
            /*总控制，可忽略此行*/
            table tr:first-child {
                background: #129bcc;
                color: #fff;
                font-weight: bold;
            }
    
            /*第一行标题蓝色背景*/
            table {
                border-top: 2pt solid #C1DAD7;
                border-left: 2pt solid #C1DAD7;
                margin: 0 auto;
                font-size: 20px;
                font-family: 黑体;
                font-weight: 600;
                line-height: 40px;
                height: 40px;
            }
    
            td {
                padding: 5px 10px;
                text-align: center;
                border-right: 1pt solid #C1DAD7;
                border-bottom: 1pt solid #C1DAD7;
            }
    
            tr:nth-of-type(odd) {
                background: #c6f9f7
            }
    
            /* odd 标识奇数行，even标识偶数行 */
            tr:hover {
                background: #E0F0F0;
            }
    
            /*鼠标悬停后表格背景颜色*/
        </style>
    </head>
    <body>
                '''
        f.write(css)
        f.write('<h3 align="center" style="font-size: 180%">{}告警信息</h3>'.format(title))
        f.write(data.replace('border="1" class="dataframe"',
                             "width=90% border='0' cellspacing='0' cellpadding='0' align='center'").replace("<tbody>",
                                                                                                            "").replace(
            "</tbody>", "").replace("<thead>", "").replace("</thead>", "").replace('<tr style="text-align: right;">',
                                                                                   '<tr style="text-align: center;">'))
        f.write("</body></html>")

    return path


def html2image(htmlPath):
    '''
    将Html转为图片
    :param htmlPath:html文件路径
    :return:
    '''
    img_path = htmlPath.replace("html", "jpg")
    try:
        config = imgkit.config(wkhtmltoimage=r'H:\tools\wkhtmltopdf\bin\wkhtmltoimage.exe')
        option = {
            "encoding": "utf-8"
        }
        imgkit.from_file(htmlPath, img_path, config=config, options=option)
    except Exception as e:
        print(e.args)
        return
    return img_path


def img2url(imgFile):
    '''
    使用七牛云平台的图床将img转为一个url
    :param imgFile:图片路径
    :return: img下载的url
    '''
    time.sleep(2)
    access_key = 'ov2oFtXDGAMLjghDR9Kiy4fTIQ3Ndo1X6UdfKy2P'
    secret_key = 'X8VqTZNlVY111XrrWz-G7G8s3m6CT5pIA2_bOPv4'
    q = Auth(access_key, secret_key)
    bucket_name = 'devopsgj'
    key = imgFile.split("/")[-1]
    downloadUrl = f"http://qg2694gqp.hn-bkt.clouddn.com/{key}"

    token = q.upload_token(bucket_name, key, 3600)
    localfile = imgFile
    print(localfile)
    ret, info = put_file(token, key, localfile)
    print("图床反馈：")
    print(ret)
    print(info)

    if info.status_code == 200:
        deadline = int(time.time()) + 24 * 60 * 60
        if '?' in downloadUrl:
            downloadUrl += '&'
        else:
            downloadUrl += '?'
        downloadUrl_ = '{0}e={1}'.format(downloadUrl, str(deadline))

        hashed = hmac.new(secret_key.encode(), downloadUrl_.encode(), hashlib.sha1)
        sign = urlsafe_base64_encode(hashed.digest())

        token = '{0}:{1}'.format(access_key, sign)
        downloadUrl_ = '{0}&token={1}'.format(downloadUrl_, token)
        print(downloadUrl_)
        return downloadUrl_
    print("图片上传失败")
    return


def sendMessage(secret, webHook, sendText, imgUrl):
    '''
    使用钉钉机器人向钉钉发送消息
    :param secret:机器人的 secret
    :param webHook: 机器人的 webHook
    :param sendText: 发送的文字
    :param imgUrl: 查看全部的url，即img2url生成的图片
    :return:
    '''
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
        "actionCard": {
            "title": "告警信息通报",
            "text": sendText,
            "btnOrientation": "0",
            "singleTitle": "查看详情" if imgUrl else "",
            "singleURL": imgUrl,
        },
        "msgtype": "actionCard"
    }

    r = requests.post(webhook, data=json.dumps(data), headers=headers)
    print(r.text)
    # time.sleep(2)


def clearDir(dataFile):
    if len(os.listdir(dataFile)) > 1:
        shutil.rmtree(dataFile)

