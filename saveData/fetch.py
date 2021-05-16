#!/usr/bin/env python
# -*- coding:utf-8 -*-
'''
中文乱码问题的两种解决方法：
1、page_text.encoding = 'utf-8'  --手动设定响应数据的编码格式
2、img_name.encode('iso-8859-1').decode('gbk')  --通用处理中文乱码的解决方案
'''




# 爬取健客网网上药店中”女性用药首页的药品相关信息“
import requests
from lxml import etree
import pymysql
from py2neo import Graph, Node, Relationship

#========================================================================
'''
# 连接mysql数据库
db = pymysql.connect(host='localhost', user='root', password='123456',
                     port=3306, db='test', charset='utf8')
# 开启mysql的游标功能，创建一个游标对象
cursor = db.cursor()

'''
#========================================================================
# 连接Neo4j数据库
graph = Graph("http://localhost:7474", user="neo4j", password='123456')

# =======================================================================
# 对首页数据进行爬取
url = 'https://www.jianke.com/list-0108.html'
headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36'
}
page_text = requests.get(url=url, headers=headers)
page_text.encoding = 'utf-8'

# 数据解析
tree = etree.HTML(page_text.text)
# 存储li标签对象
li_list = tree.xpath('//ul[@class="pro-con"]/li')

for li in li_list:
        url_detail = 'https:' + li.xpath('./div/div[2]/p/a/@href')[0]
        # print(url_detail)
        # 请求详情页面
        page_text_detail = requests.get(url=url_detail, headers=headers)
        page_text_detail.encoding = 'utf-8'
        # 详情数据解析
        tree_detail = etree.HTML(page_text_detail.text)

        str = '//table[@class="table_cal"]'
        # 药品名称
        name = tree_detail.xpath(str + '/tr[1]/td[2]/text()')[0]
        # 价格
        money = tree_detail.xpath('//dl[@id="jk_syncdata"]/div/div/dl/dd/em/text()')[0]+''
        price = money[1:]
        # 主要成分
        component = tree_detail.xpath(str + '/tr[2]/td[2]/text()')[0]
        # 主要功效
        func = tree_detail.xpath(str + '/tr[3]/td[2]/text()')[0]
        # 生产厂家
        manu = tree_detail.xpath(str + '/tr[6]/td[2]/text()')[0]
        # print(name)
        # print(price)
        # print(component)
        # print(func)
        # print(manu)

        # 创建药品节点，其中属性包括：name, price, component, func, manu
        d = Node('drug', name=name, price=price, component=component, function=func)
        # 创建生产厂商节点
        m = Node('manufacturer', name=manu)
        # 创建药品节点和生产厂商节点的关系
        r = Relationship(m, 'manufacture', d)
        # 向Neo4j数据库中插入数据
        s = d | m | r
        graph.create(s)
        print('over!')
'''

        # 将数据存入mysql数据库中
        try:
                # print('=======')
                cursor.execute("INSERT INTO drug_info VALUES('%s', '%s', '%s', '%s', '%s')" % (name, price, component, func, manu))
                db.commit()
                print("插入成功")

        except:
                print("插入失败")
                db.rollback()
cursor.close()
db.close()


'''



