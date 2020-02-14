#!/usr/bin/env python3
#-*-coding:utf-8-*-

import eventlet
eventlet.monkey_patch()

from bs4 import BeautifulSoup
from lxml import etree
import requests, os, time, concurrent.futures

def login():
    '''登录'''
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
    global list_url
    for i in page:
        print(f'正在采集第{i}页')
        if i == 1:
            # 001代表NSFW 1y代表过去一年 1M代表过去一月 1w代表过去一周 1d代表过去一天 toplist
            url = 'https://wallhaven.cc/search?categories=111&purity=001&topRange=6M&sorting=toplist&order=desc&page'
        else:
            url = f'https://wallhaven.cc/search?categories=111&purity=001&topRange=6M&sorting=toplist&order=desc&page={i}'
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


def delete_url():
    '''删除重复url'''
    global list_url
    # 我准备了一份过去一年toplist前30页，每页32张的文本，用来剔除下载不同时期的重复图片
    with open('1Y1-30.txt', 'r') as f:
        toplist = f.read()

    delete_who = []
    for i in list_url:
        if i in toplist:
            delete_who.append(i)
            list_url.remove(i)

    print(f'删除{len(delete_who)}个重复url')



def get_img(url_list):
    '''下载图片'''
    global download
    for i in url_list:
        try:
            with eventlet.Timeout(120, True):
                name = i.split('/')
                filename = b + name[-1] + '.jpg'
                print(f'开始下载：{name[-1]}')

                img_req = session.get(url = i, headers=headers)
                img_req.encoding = 'utf-8'
                img_html = img_req.content
                img_bf_1 = BeautifulSoup(img_html, 'lxml')
                img_url = img_bf_1.find_all('div', class_='scrollbox')
                img_bf_2 = BeautifulSoup(str(img_url), 'lxml')
                img_url = img_bf_2.img.get('src')
                response = session.get(img_url, headers=headers)

                with open(filename, "wb") as f :
                    f.write(response.content)

                download += 1
                print(f'第{download}张图片下载完成：{name[-1]}')
        except:
            print(f'{name[-1]}下载失败')
            fail_url_list.append(i)

if __name__ == '__main__':
    # 开始计时
    start_time = time.time()

    # 采集的页数
    page = list(range(1,6))
    page_name = f'{page[0]}-{page[-1]}'

    # 图片url列表
    list_url = []

    # 计数器
    download = 0

    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'}

    login()
    get_url()
    delete_url()
    print(f'即将下载{len(list_url)}张图片')

    #新建文件夹
    b = os.path.abspath('.') + '\\' + page_name +'\\'
    if not os.path.exists(b):
        os.makedirs(b)

    fail_url_list = []

    # 将list_url 重写为 包含4个list的list
    n = len(list_url) // 8
    n2 = n*2
    n3 = n*3
    n4 = n*4
    n5 = n*5
    n6 = n*6
    n7 = n*7
    new_list = [list_url[0:n], list_url[n:n2], list_url[n2:n3], list_url[n3:n4], list_url[n4:n5], list_url[n5:n6], list_url[n6:n7], list_url[n7:len(list_url)]]

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as e:
        [e.submit(get_img, i) for i in new_list]

    print(f'用时{time.time() - start_time}秒')

    if fail_url_list:
        print(f'{len(fail_url_list)}张图片下载失败\n{fail_url_list}')
    print(f'{download}张图片下载成功')
    
    input('回车以结束程序')