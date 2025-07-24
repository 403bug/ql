#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File: kaduoduo.py(卡多多订单查询)
Author: sjmy
cron: 20 */3 * * *
new Env('卡多多订单查询');
Update: 2025/07/18

"""


from bs4 import BeautifulSoup
import requests

import notify

Log = ""

def set_log(text):
    print(text)
    global Log
    Log = Log + "\n" + text


# 获取日志
def get_log():
    # return Log.replace("\n","\r\n") # 用于 windows 和 Linux 换行符切换
    return Log.replace("\n", "\n\n")  # 用于适配markdown格式输出



url = "https://ka.kaduoduohk.com/orderlist"

payload = {
  'mobile': "15921063045",
  'IdCard': "411628200512206911",
  'uid': "cWxocS9xTHVHSVk9",
  'csrf_order_token': "07943eb1547e473384acba2336a41b80cb8c6277aabdbd016d7e25395ca003c0"
}

headers = {
  'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
  'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
  'Accept-Encoding': "gzip, deflate, br, zstd",
  'cache-control': "max-age=0",
  'sec-ch-ua': "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Microsoft Edge\";v=\"138\"",
  'sec-ch-ua-mobile': "?0",
  'sec-ch-ua-platform': "\"Windows\"",
  'upgrade-insecure-requests': "1",
  'origin': "https://ka.kaduoduohk.com",
  'sec-fetch-site': "same-origin",
  'sec-fetch-mode': "navigate",
  'sec-fetch-user': "?1",
  'sec-fetch-dest': "document",
  'referer': "https://ka.kaduoduohk.com/cha?k=cWxocS9xTHVHSVk9",
  'accept-language': "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5",
  'priority': "u=0, i",
  'Cookie': "AGL_USER_ID=b0fa071e-4695-4bc3-90e0-798b141b4764; PHPSESSID=4n5rmjleve4dr2mhamrqu5r2go"
}

# 发送请求
response = requests.post(url, data=payload, headers=headers)

# 检查响应状态码
if response.status_code == 200:
    # 明确指定编码
    response.encoding = 'utf-8'
    html_content = response.text
    # set_log("响应内容：")
    # set_log(html_content)  # 打印响应内容，用于调试

    # 解析HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # 存储所有订单数据的列表
    orders = []

    # 提取每个订单的容器（class为search-result的div）
    order_containers = soup.find_all('div', class_='search-result')

    for container in order_containers:
        # 提取订单基本信息
        item_title = container.find('div', class_='item-title')
        if not item_title:
            continue

        # 提取产品名称
        product_name_element = item_title.find('p', style=lambda s: 'font-size' in str(s) and '20px' in str(s))
        product_name = product_name_element.get_text(strip=True) if product_name_element else "未找到产品名称"

        # 初始化下单时间和订单编号为默认值
        time_span = "未找到下单时间"
        order_id = "未找到订单编号"

        # 获取 item-title 下所有 p 标签
        p_tags = item_title.find_all('p')
        for p in p_tags:
            p_text = p.get_text(strip=True)
            if "下单时间" in p_text:
                span = p.find('span')
                if span:
                    time_span = span.get_text(strip=True)
            elif "订单编号" in p_text:
                span = p.find('span')
                if span:
                    order_id = span.get_text(strip=True)

        # 提取详情信息（collapse类的div）
        span_element = container.find('span', class_='item-content')
        detail_id = span_element['data-target'].lstrip('#') if span_element and 'data-target' in span_element.attrs else None
        detail_div = container.find('div', id=detail_id) if detail_id else None

        # 初始化详情字典
        details = {
            '产品名称': product_name,
            '下单时间': time_span,
            '订单编号': order_id
        }

        if detail_div:
            # 提取详情中的各项信息
            detail_items = detail_div.find_all('div', class_='item')
            for item in detail_items:
                label_div = item.find('div', class_='label')
                content_div = item.find('div', class_='content')
                if label_div and content_div:
                    label = label_div.get_text(strip=True)
                    content = content_div.get_text(strip=True)
                    details[label] = content

        # 将订单信息添加到列表
        orders.append(details)
    # 打印提取的订单数据
    set_log("提取的订单数据：")
    for order in orders:
        for key, value in order.items():
            set_log(f"{key}: {value}")
        set_log("-" * 30)
else:
    set_log(f"请求失败，状态码：{response.status_code}")

notify.send("卡多多订单查询", get_log())
