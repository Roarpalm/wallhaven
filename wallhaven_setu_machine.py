#!/usr/bin/env python3
#-*-coding:utf-8-*-

import eventlet
eventlet.monkey_patch()

from bs4 import BeautifulSoup
from lxml import etree
import requests, os, time, threading

def login():
    global session

    print('开始登录...')
    # 请求登录页面，获取cookie
    login_index_url = 'https://wallhaven.cc/login'
  
    #为了保存cookie，用requests.session进行请求
    session = requests.session()
    login_index_response = session.get(login_index_url, headers=headers)
    result = login_index_response.content.decode()
    html = etree.HTML(result)
 
    _token = html.xpath(r'//*[@id="login"]/input[1]')[0].attrib
    _token = _token['value']

    data = {
        '_token' : _token,
        'username': '', # 账号
        'password': ''  # 密码
    }

    # 请求登录的url
    login_url = 'https://wallhaven.cc/auth/login'
  
    session.post(login_url, headers=headers, data=data)
    print('登录成功')



def get_url():
    '''采集排行榜里的图片链接'''

    global list_url, session
    # 采集的页数，括号内自己改
    for i in range(1,10):
        print(f'正在采集第{i}页')
        if i == 1:
            # 001代表NSFW 1y代表过去一年 toplist
            url = 'https://wallhaven.cc/search?categories=111&purity=001&topRange=1y&sorting=toplist&order=desc&page'
        else:
            url = f'https://wallhaven.cc/search?categories=111&purity=001&topRange=1y&sorting=toplist&order=desc&page={i}'
        req = session.get(url=url, headers=headers)
        req.encoding = 'utf-8'
        html1 = req.content
        bf = BeautifulSoup(html1, 'lxml')
        #搜索所有figure
        targets_url = bf.find_all('figure')

        for each in targets_url:
            # 提取其中的href链接并保存在list
            list_url.append(each.a.get('href'))
        print(f'第{i}页采集完成')



def get_img(url_list):
    '''下载图片'''
    global download, session
    for i in url_list:
        with eventlet.Timeout(120,False):
            download += 1
            name = i.split('/')
            filename = name[-1] + '.jpg'
            print(f'{threading.currentThread().getName()}下载第{download}张图片：{filename}')
            img_req = session.get(url = i, headers=headers)
            img_req.encoding = 'utf-8'
            img_html = img_req.content
            img_bf_1 = BeautifulSoup(img_html, 'lxml')
            img_url = img_bf_1.find_all('div', class_='scrollbox')
            img_bf_2 = BeautifulSoup(str(img_url), 'lxml')
            img_url = img_bf_2.img.get('src')
            response = session.get(img_url, headers=headers)

            #判断当前路径是否存在，没有则创建new文件夹
            b = os.path.abspath('.') + '\\new\\'
            if not os.path.exists(b):
                os.makedirs(b)
            filename = b + filename
            with open(filename, "wb") as f :
                f.write(response.content)

            print(f'{threading.currentThread().getName()}下载完成：{filename}')
            success_url.append(i)
            fail_url = i
            fail_url_list.remove(fail_url)
            time.sleep(2)


            
if __name__ == '__main__':
    # 开始计时
    start_time = time.time()

    # 图片url列表
    list_url = []

    # 计数器
    download = 0

    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'}

    login()
    get_url()
    print(f'即将下载{len(list_url)}张图片')
    print(list_url)

    fail_url_list = list_url
    success_url = []

    # 将list_url 重写为 包含4个list的list
    n = int(len(list_url) / 4)
    n2 = n * 2
    n3 = n * 3
    new_list = [list_url[0:n], list_url[n:n2], list_url[n2:n3], list_url[n3:len(list_url)]]

    # 开启4个线程
    th = []
    th_num = 0
    for i in new_list:
        th_num += 1
        t = threading.Thread(name=f'线程{th_num}', target=get_img, args=(i,))
        th.append(t)
    for i in th:
        i.start()
    for i in th:
        i.join()

    end_time = time.time()
    print(f'用时{end_time - start_time}秒')

    if fail_url_list:
        print(f'{len(fail_url_list)}张图片下载失败\n{fail_url_list}')
    print(f'{len(success_url)}张图片下载成功\n{success_url}')
    
    input('回车以结束程序')