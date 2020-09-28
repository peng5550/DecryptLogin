# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


'''定义要爬取的数据'''
class DazhongdianpingItem(scrapy.Item):
    # 店名
    shopname = scrapy.Field()
    # 点评数量
    num_comments = scrapy.Field()
    # 人均价格
    avg_price = scrapy.Field()
    # 美食类型
    food_type = scrapy.Field()
    # 所在商区
    business_district_name = scrapy.Field()
    # 具体位置
    location = scrapy.Field()
    # 口味评分
    taste_score = scrapy.Field()
    # 环境评分
    environment_score = scrapy.Field()
    # 服务评分
    serve_score = scrapy.Field()