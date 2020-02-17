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



def get_img(url_list):
    '''下载图片'''
    global download
    for i in url_list:
        try:
            with eventlet.Timeout(180, True):
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
            print(f'下载失败：{name[-1]}')
            fail_url_list.append(i)



def main():
    # 将list_url 重写为 包含8个list的list
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

if __name__ == '__main__':
    # 开始计时
    start_time = time.time()

    # 采集的页数
    page = list(range(1,6))
    page_name = f'{page[0]}-{page[-1]}'

    # 图片url列表
    list_url = []

    #新建文件夹
    b = os.path.abspath('.') + '\\' + page_name +'\\'
    if not os.path.exists(b):
        os.makedirs(b)

    # 计数器
    download = 0

    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'}

    login()
    print(f'即将下载{len(list_url)}张图片')

    fail_url_list = []

    main()

    while True:
        if len(fail_url_list) > 10:
            print(f'{len(fail_url_list)}张图片下载失败\n{fail_url_list}')
            last_download = download
            list_url = fail_url_list
            fail_url_list = []
            print('再次下载...')
            main()
            print(f'成功下载{download - last_download}张图片')
        else:
            print(f'{len(fail_url_list)}张图片下载失败\n{fail_url_list}')
            break
        
    print(f'用时{time.time() - start_time}秒')
    print(f'{download}张图片下载成功')
    
    input('回车以结束程序')