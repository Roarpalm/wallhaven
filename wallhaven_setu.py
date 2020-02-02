#!/usr/bin/env python3
#-*-coding:utf-8-*-
#author: Roarpalm
from bs4 import BeautifulSoup
from urllib.request import urlretrieve
from lxml import etree
import requests
import os
import time
import threading

# 计时器
start_time = time.time()

# 创建一个url列表用来储存url
list_url = []

# 计数器
start = -1

headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'}

# 请求登录页面，获取cookie
login_index_url = 'https://wallhaven.cc/login'
login_index_headers = {
    'referer': 'https://wallhaven.cc/login',
    'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
}
 
# 为了保存cookie我们用requests.session进行请求
session = requests.session()
login_index_response = session.get(login_index_url, headers=login_index_headers)
result = login_index_response.content.decode()
html = etree.HTML(result)

# 获取_token, 只有账号密码不足以登录wallha
_token = html.xpath(r'//*[@id="login"]/input[1]')[0].attrib
_token = _token['value']

data = {
    '_token' : _token,
    'username': '###', # 此处填写账号
    'password': '###' # 此处填写密码
}

# 请求登录的url
login_url = 'https://wallhaven.cc/auth/login'
login_response = session.post(login_url, headers=headers, data=data)



def get_url():
    '''采集网页图片链接'''

    global list_url
    for i in range(1,2):
        print(f'正在采集第{i}页')
        if i == 1:
            url = 'https://wallhaven.cc/search?categories=111&purity=001&topRange=1M&sorting=toplist&order=desc&page' #001代表NSFW 100代表SFW
        else:
            url = f'https://wallhaven.cc/search?categories=111&purity=001&topRange=1M&sorting=toplist&order=desc&page={i}'
        req = session.get(url=url, headers=headers)
        req.encoding = 'utf-8'
        html1 = req.content
        bf = BeautifulSoup(html1, 'lxml')
        # 搜索所有figure
        targets_url = bf.find_all('figure')

        # 提取其中的href链接并保存在list
        for each in targets_url:
            list_url.append(each.a.get('href'))
        print('第%d页采集完成' % (i))



def get_img():
    '''下载图片'''

    global list_url, start

    # 把url列表分成4份对应下面4个进程
    num = len(list_url) // 4

    for _ in range(num):
        start += 1
        name = list_url[start].split('/')
        filename = name[-1] + '.jpg'
        print('下载：' + filename)
        img_req = session.get(url = list_url[start], headers=headers)
        img_req.encoding = 'utf-8'
        img_html = img_req.content
        img_bf_1 = BeautifulSoup(img_html, 'lxml')
        img_url = img_bf_1.find_all('div', class_='scrollbox')
        img_bf_2 = BeautifulSoup(str(img_url), 'lxml')
        img_url = img_bf_2.img.get('src')
        response = session.get(img_url, headers=headers)
        with open(filename, "wb") as f :
            f.write(response.content)   
            f.close()
        print(filename + '下载完成！')



if __name__ == '__main__':
    get_url()
    print(f'即将下载{len(list_url)}张图片')
    num = len(list_url) // 4

    # 开启4个线程, 可以自己尝试不同数量
    ts = []
    for _ in range(4):
        th = threading.Thread(target=get_img)
        ts.append(th)
    for i in ts:
        i.start()
    for i in ts:
        i.join()

    # 下载剩余的几张图
    if num:
        abc = num % 4
        for _ in range(abc):
            name = list_url[num - abc].split('/')
            filename = name[-1] + '.jpg'
            print('下载：' + filename)
            img_req = session.get(url = list_url[num - abc], headers=headers)
            img_req.encoding = 'utf-8'
            img_html = img_req.content
            img_bf_1 = BeautifulSoup(img_html, 'lxml')
            img_url = img_bf_1.find_all('div', class_='scrollbox')
            img_bf_2 = BeautifulSoup(str(img_url), 'lxml')
            img_url = img_bf_2.img.get('src')
            response = session.get(img_url, headers=headers)
            with open(filename, "wb") as f :
                f.write(response.content)   
                f.close()
            print('完成：' + filename)
            time.sleep(1)
            abc -= 1

    end_time = time.time()
    print(f'用时{end_time - start_time}秒')