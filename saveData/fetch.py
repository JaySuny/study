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
import re
import pymysql
from py2neo import Graph, Node, Relationship
import json

#========================================================================

# 连接mysql数据库
db = pymysql.connect(host='localhost', user='root', password='123456',
                     port=3306, db='test', charset='utf8')
# 开启mysql的游标功能，创建一个游标对象
cursor = db.cursor()


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

features = ['含', '成分', '成份', '辅料', '。', 'g', '形式', '化学名']
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
        component = tree_detail.xpath(str + '/tr[2]/td[2]/text()')[0]+''
        # print(component)
        # print('-----------------------')

        # 拆分数据，提取药品成分
        com_str_list = []
        if component.find(features[3]) != -1:
            # print(component.find(features[4]))
            # print('--------------------')
            if component.find(features[1]) != -1:
                component = component[component.find(features[1])+2:]
            elif component.find(features[0]) != -1:
                component = component[component.find(features[0]) + 1:]
            # component = component[component.find(features[])]
            com_str_list = list(filter(None, re.split('、|。|为|：|\d|\.|毫克|辅料', component)))
            # print(com_str_list)

        elif component.find(features[1]) != -1 or component.find(features[2]) != -1:
            # print('--------------------')
            # print(component)
            if component.find(features[5]) == -1 and component.find(features[6]) == -1:
                component = component[component.find('成')+3:component.find(features[4])]
                # print(component)
            elif component.find(features[6]) != -1:
                component = component[component.find('，') + 2:component.find(features[6])]

            com_str_list = list(filter(None, re.split('。|为|：|\d|mg|，', component)))
            if len(com_str_list) > 1:
                com_str_list.pop(0)
                com_str_list.pop(1)
                com_str_list.pop(1)
            # print(com_str_list)

        elif component.find(features[0]) != -1:
            if component.find(features[6]) != -1:
                index = component.find(features[0], component.find(features[0]) + 1)
                component = component[index:component.find(features[4])]

            component = component[component.rfind(features[0]):]
            com_str_list = re.split('。|含|有|\d|\.|和|mg', component)
            com_str_list = [comp for comp in com_str_list if comp != ' ']
            # print(com_str_list)
        elif component.find(features[5]) != -1:
            component = component[component.find(features[5])+1:]
            com_str_list = re.split('。|和|\d|mg|\.', component)
            com_str_list.remove(' ')
            # print(com_str_list)
        else:
            if component.find(features[7]):
                component = component[:component.find(features[4])]
                # print(component)
            com_str_list = re.split('。|、', component)
            # print(com_str_list)
            if '\t' in com_str_list:
                com_str_list.remove('\t')
        # print(com_str_list)

        com_str_list = list(filter(None, com_str_list))
        # 中文字符问题的处理：ensure_ascii=False
        jsonStr = json.dumps(com_str_list, ensure_ascii=False)
        # print(jsonStr)

        # 主要功效
        func = tree_detail.xpath(str + '/tr[3]/td[2]/text()')[0]
        # 生产厂家
        manu = tree_detail.xpath(str + '/tr[6]/td[2]/text()')[0]
        # print(name)
        # print(price)
        # print(component)
        # print(func)
        # print(manu)

        # 将数据存入mysql数据库中
        try:
            print('=======')
            cursor.execute(
                "INSERT INTO drug_info VALUES('%s', '%s', '%s', '%s', '%s')" % (name, price, jsonStr, func, manu))
            db.commit()
            print("插入成功")

        except:
            print("插入失败")
            db.rollback()
            cursor.close()
db.close()


'''
        # 创建药品节点，其中属性包括：name, price, func, manu
        d = Node('drug', name=name, price=price, function=func)
        # 创建生产厂商节点
        m = Node('manufacturer', name=manu)
        # 创建药品节点和生产厂商节点的关系
        r = Relationship(m, 'manufacture', d)
        # 向Neo4j数据库中插入数据
        s = d | m | r
        graph.create(s)

        # 创建药品成分节点
        for name in com_str_list:
            c = Node('component', name=name)
            r = Relationship(d, 'include', c)
            s = d | c | r
            graph.create(s)

        print('over!')
'''










