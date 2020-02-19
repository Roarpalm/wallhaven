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
    try:
        # 请求登录页面，获取cookie
        login_index_url = 'https://wallhaven.cc/login'
  
        #为了保存cookie，用requests.session进行请求
        session = requests.session()
        login_index_response = session.get(login_index_url, headers=headers)
        result = login_index_response.content.decode()
        html = etree.HTML(result)

        # 获取token
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
    except:
        print('登录失败')
    else:
        print('登录成功')

def get_url():
    '''采集排行榜里的图片链接'''
    global list_url
    for i in page:
        print(f'正在采集第{i}页')
        if i == 1:
            # 001代表NSFW 1y代表过去一年 1M代表过去一月 1w代表过去一周 1d代表过去一天 toplist
            url = 'https://wallhaven.cc/search?categories=111&purity=001&topRange=1M&sorting=toplist&order=desc&page'
        else:
            url = f'https://wallhaven.cc/search?categories=111&purity=001&topRange=1M&sorting=toplist&order=desc&page={i}'
        req = session.get(url=url, headers=headers).text
        bf = BeautifulSoup(req, 'lxml')
        # 搜索所有figure
        targets_url = bf.find_all('figure')
        for each in targets_url:
            # 提取其中的href链接并保存在list
            list_url.append(each.a.get('href'))
        print(f'第{i}页采集完成')

def write_url():
    '''保存已爬url'''
    global list_url
    # 读取已爬的url，如果重复，则删除
    with open('all-url.txt', 'r') as f:
        all_list = f.read().splitlines()
        delete_who = 0
        for i in list_url:
            if i in all_list:
                delete_who += 1
                list_url.remove(i)
        print(f'删除{delete_who}个重复url')

    # 将新爬的url添加到列表末尾并写入
    with open('all-url.txt', 'w') as f:
        all_list.extend(list_url)
        for i in all_list:
            f.write(f'{i}\n')
        print(f'新增{len(list_url)}个url到文本')

def get_img(url):
    '''解析网页获取图片url'''
    global ture_url
    img_html = session.get(url=url, headers=headers).text
    img_bf_1 = BeautifulSoup(img_html, 'lxml')
    div = img_bf_1.find_all('img', {'id':'wallpaper'})
    for urls in div:
        img_url = urls['src']
    ture_url.append(img_url)

def img_download(url):
    '''下载图片'''
    global fail_url_list, download
    name = url.split('/')
    filename = b + name[-1]
    print(f'开始下载：{name[-1]}')
    try:
        with eventlet.Timeout(180, True):
            response = session.get(url, headers=headers)
            with open(filename, "wb") as f :
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
            download += 1
            print(f'第{download}张图片下载完成：{name[-1]}')
    except:
        print(f'下载失败：{name[-1]}')
        fail_url_list.append(url)

def write_fail_url():
    '''保存失败url'''
    with open('fail.txt', 'r') as f:
        fail_list = f.read().splitlines()
        delete_who = 0
        for i in fail_url_list:
            if i in fail_list:
                delete_who += 1
                list_url.remove(i)
        print(f'删除{delete_who}个重复url')
    with open('fail.txt', 'w') as f:
        fail_list.extend(fail_url_list)
        for i in fail_list:
            f.write(f'{i}\n')

def main():
    '''开8个线程下载'''
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as e:
        [e.submit(img_download, url) for url in ture_url]

if __name__ == '__main__':
    # 开始计时
    start_time = time.time()

    # 在此更改采集的页数
    page = list(range(1, 31))
    page_name = f'{page[0]}-{page[-1]}'

    # 网页url列表
    list_url = []
    # 图片url列表
    ture_url = []

    # 计数器
    download = 0

    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'}

    login()
    get_url()
    write_url()
    print(f'即将下载{len(list_url)}张图片')

    # 新建文件夹
    b = os.path.abspath('.') + '\\' + page_name +'\\'
    if not os.path.exists(b):
        os.makedirs(b)

    fail_url_list = []

    # 解析网页这一步如果开多线程去做就会频繁解析失败，线程开得越多失败率越高
    [get_img(url) for url in list_url]
    print(f'{len(ture_url)}个图片url解析成功')

    main()

    while True:
        if len(fail_url_list) > 10:
            print(f'{len(fail_url_list)}张图片下载失败\n{fail_url_list}')
            last_download = download
            list_url = fail_url_list
            fail_url_list = []
            print('再次下载...')
            main()
            print(f'{download - last_download}张图片下载成功')
        else:
            print(f'{len(fail_url_list)}张图片下载失败\n{fail_url_list}')
            write_fail_url()
            break

    print(f'用时{time.time() - start_time}秒')
    print(f'{download}张图片下载成功')
    
    input('回车以结束程序')