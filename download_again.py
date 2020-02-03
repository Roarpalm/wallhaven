#!/usr/bin/env python3
#-*-coding:utf-8-*-

import eventlet
eventlet.monkey_patch()

from bs4 import BeautifulSoup
from lxml import etree
import requests, os, time, threading

# 开始计时
start_time = time.time()

# 图片url列表, 在此处修改。下面这张图就是个例子，图片文件太大了
list_url = ['https://wallhaven.cc/favorites/fav/73o1ev']

# 计数器
download = 0

headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'}

# 请求登录页面，获取cookie
login_index_url = 'https://wallhaven.cc/login'
login_index_headers = {
    'referer': 'https://wallhaven.cc/login',
    'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
}
 
#为了保存cookie我们用requests.session进行请求
session = requests.session()
login_index_response = session.get(login_index_url, headers=login_index_headers)
result = login_index_response.content.decode()
html = etree.HTML(result)

#获取_token
_token = html.xpath(r'//*[@id="login"]/input[1]')[0].attrib
_token = _token['value']

data = {
    '_token' : _token,
    'username': '', #账号
    'password': '' #密码
}

# 请求登录的url
login_url = 'https://wallhaven.cc/auth/login'
login_response = session.post(login_url, headers=headers, data=data)


# 之前采用计数器的方式让4个线程重复执行一段代码，但总是发生 index error
# 干脆简单粗暴地拆分成4个函数让4个线程各自执行
def get_img():
    global download
    for i in list_url:
        # 下载超过600秒自动跳过
        with eventlet.Timeout(600,False):
            try:
                download += 1
                # 图片重命名
                name = i.split('/')
                filename = name[-1] + '.jpg'

                print(f'下载第{download}张图片：{filename}')
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
                    f.close()
                print(f'完成图片：{filename}')
                success_url.append(i)
                fail_url = i
                fail_url_list.remove(fail_url)
                time.sleep(5)
            except:
                continue
            
if __name__ == '__main__':
    print(f'即将下载{len(list_url)}张图片')
    print(list_url)

    fail_url_list = list_url
    success_url = []

    get_img()

    end_time = time.time()
    print(f'用时{end_time - start_time}秒')

    if fail_url_list:
        print(f'{len(fail_url_list)}张图片下载失败\n{fail_url_list}')
    print(f'{len(success_url)}张图片下载成功\n{success_url}')

    input('回车以结束程序')