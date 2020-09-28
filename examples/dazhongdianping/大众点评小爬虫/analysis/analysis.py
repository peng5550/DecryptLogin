'''
Function:
    大众点评美食数据可视化
Author:
    Charles
微信公众号:
    Charles的皮卡丘
'''
import os
import json
import requests
from pyecharts import options
from pyecharts.globals import ThemeType
from pyecharts.charts import Bar, Pie, Funnel, BMap


'''百度开发者AK'''
BAIDU_AK = '申请的百度开发者AK'


'''检查文件在是否存在'''
def checkDir(dirpath):
    if not os.path.exists(dirpath):
        os.mkdir(dirpath)
        return False
    return True


'''画饼图'''
def drawPie(title, data, savedir='./results'):
    checkDir(savedir)
    pie = (Pie(init_opts=options.InitOpts(theme=ThemeType.VINTAGE))
          .add('', [list(item) for item in data.items()], radius=['30%', '75%'], center=['50%', '50%'], rosetype='radius')
          .set_global_opts(title_opts=options.TitleOpts(title=title, pos_left='center'), legend_opts=options.LegendOpts(orient='vertical', pos_top='5%', pos_left='2%')))
    pie.render(os.path.join(savedir, title+'.html'))


'''画柱状图'''
def drawBar(title, data, savedir='./results'):
    checkDir(savedir)
    bar = (Bar(init_opts=options.InitOpts(theme=ThemeType.VINTAGE))
          .add_xaxis(list(data.keys()))
          .set_global_opts(xaxis_opts=options.AxisOpts(axislabel_opts=options.LabelOpts(rotate=-15)),
                           title_opts=options.TitleOpts(title=title, pos_left='center'), legend_opts=options.LegendOpts(orient='vertical', pos_top='15%', pos_left='0%')))
    if type(list(data.values())[0]) != type(list()):
        bar.add_yaxis('', list(data.values()))
    else:
        for i in range(len(list(data.values())[0])):
            bar.add_yaxis(list(data.values())[0][i][0], [value[i][1] for key, value in data.items()])
    bar.render(os.path.join(savedir, title+'.html'))


'''画漏斗图'''
def drawFunnel(title, data, savedir='./results'):
    checkDir(savedir)
    funnel = (Funnel(init_opts=options.InitOpts(theme=ThemeType.MACARONS))
             .add('', [list(item) for item in data.items()], label_opts=options.LabelOpts(position="inside"))
             .set_global_opts(title_opts=options.TitleOpts(title=title, pos_left='center'), legend_opts=options.LegendOpts(orient='vertical', pos_top='15%', pos_left='2%')))
    funnel.render(os.path.join(savedir, title+'.html'))


'''获得对应地址的经纬度'''
def getLatLngByName(name):
    url = 'http://api.map.baidu.com/geocoding/v3/?address=%s&output=json&ak=%s'
    response = requests.get(url % (name, BAIDU_AK))
    loc = response.json()['result']['location']
    return loc['lng'], loc['lat']


'''百度地图'''
def drawBaiduMAP(title, data, savedir='./results'):
    checkDir(savedir)
    center = [sum([value[0] for key, value in data.items()]) / len(data),
              sum([value[1] for key, value in data.items()]) / len(data)]
    map_ = (BMap().add_schema(baidu_ak=BAIDU_AK,
                              center=center,
                              zoom=12,
                              is_roam=True))
    for key, value in data.items():
        map_.add_coordinate(name=key, longitude=value[0], latitude=value[1])
        map_.add('', [[key, value[2]]], type_='effectScatter', label_opts=options.LabelOpts(is_show=False))
    map_.render(os.path.join(savedir, title+'.html'))


'''run'''
if __name__ == '__main__':
    # 数据导入
    all_infos = json.load(open('infos.json', 'r'))
    # 美食数量最多的十个商区
    data = {}
    for info in all_infos:
        business_district_name = info.get('business_district_name')
        if business_district_name in data:
            data[business_district_name] += 1
        else:
            data[business_district_name] = 1
    data = dict(sorted(data.items(), key=lambda item: -item[1])[:10])
    drawBar('美食数量最多的十个商区', data)
    # 美食店铺百度地图可视化
    data = {}
    for info in all_infos:
        business_district_name = info.get('business_district_name')
        if business_district_name in data:
            data[business_district_name][2] += 1
        else:
            try:
                loc = getLatLngByName('杭州'+business_district_name)
                if loc[0] > 122 or loc[0] < 28 or loc[1] > 32 or loc[1] < 28:
                    continue
                data[business_district_name] = [*loc, 1]
            except:
                continue
    drawBaiduMAP('美食店铺百度地图可视化', data)
    # 美食综合评分最高的10个商区
    data = {}
    for info in all_infos:
        business_district_name = info.get('business_district_name')
        try:
            if business_district_name in data:
                data[business_district_name][0].append(float(info.get('taste_score')))
                data[business_district_name][1].append(float(info.get('environment_score')))
                data[business_district_name][2].append(float(info.get('serve_score')))
            else:
                data[business_district_name] = [[float(info.get('taste_score'))], [float(info.get('environment_score'))], [float(info.get('serve_score'))]]
        except:
            continue
    for key, value in data.items():
        data[key][0] = round(sum(data[key][0]) / len(data[key][0]), 2)
        data[key][1] = round(sum(data[key][1]) / len(data[key][1]), 2)
        data[key][2] = round(sum(data[key][2]) / len(data[key][2]), 2)
    data = dict(sorted(data.items(), key=lambda item: -sum(item[1]))[:8])
    for key, value in data.items():
        data[key] = [['口味评分', value[0]], ['环境评分', value[1]], ['服务评分', value[2]]]
    drawBar('美食综合评分最高的8个商区', data)
    # 人均消费价格分布
    data = {'50元以下': 0, '50-100元': 0, '100-150元': 0, '150-200元': 0, '200元以上': 0}
    for info in all_infos:
        if info.get('avg_price') == 'null' or not info.get('avg_price'):
            continue
        avg_price = float(info.get('avg_price'))
        if avg_price < 50:
            data['50元以下'] += 1
        elif avg_price < 100:
            data['50-100元'] += 1
        elif avg_price < 150:
            data['100-150元'] += 1
        elif avg_price < 200:
            data['150-200元'] += 1
        elif avg_price >= 200:
            data['200元以上'] += 1
    drawPie('人均消费价格分布', data)
    # 去的人最多的十家店
    data = {}
    for info in all_infos:
        if not info.get('num_comments') or info.get('num_comments') == 'null':
            continue
        data[info.get('shopname')] = float(info.get('num_comments'))
    data = dict(sorted(data.items(), key=lambda item: -item[1])[:10])
    drawBar('去的人最多的十家店', data)
    # 杭州哪些菜系比较多
    data = {}
    for info in all_infos:
        if not info.get('food_type') or info.get('food_type') == 'null':
            continue
        if info.get('food_type') in data:
            data[info.get('food_type')] += 1
        else:
            data[info.get('food_type')] = 1
    data = dict(sorted(data.items(), key=lambda item: -item[1])[:10])
    drawFunnel('杭州哪些菜系比较多', data)