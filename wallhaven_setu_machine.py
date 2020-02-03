#!/usr/bin/env python3
#-*-coding:utf-8-*-

import eventlet
eventlet.monkey_patch()

from bs4 import BeautifulSoup
from lxml import etree
import requests, os, time, threading

# 开始计时
start_time = time.time()

# 图片url列表
list_url = []

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



def get_url():
    '''采集排行榜里的图片链接'''

    global list_url
    # 采集的页数
    for i in range(2, 3):
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


# 之前采用计数器的方式让4个线程重复执行一段代码，但总是发生 index error
# 干脆简单粗暴地拆分成4个函数让4个线程各自执行
def get_img1():
    '''线程1'''
    global download
    for i in list1:
        # 下载超过120秒自动跳过
        with eventlet.Timeout(120,False):
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

def get_img2():
    '''线程2'''
    global download
    for i in list2:
        with eventlet.Timeout(120,False):
            try:
                download += 1
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

def get_img3():
    '''线程3'''
    global download
    for i in list3:
        with eventlet.Timeout(120,False):
            try:
                download += 1
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

def get_img4():
    '''线程4'''
    global download
    for i in list4:
        with eventlet.Timeout(120,False):
            try:
                download += 1
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
    get_url()
    print(f'即将下载{len(list_url)}张图片')
    print(list_url)

    fail_url_list = list_url
    success_url = []

    # 拆分url成4个列表分给4个线程
    num = int(len(list_url) / 4)
    num2 = num * 2
    num3 = num * 3
    list1 = list_url[0:num]
    list2 = list_url[num:num2]
    list3 = list_url[num2:num3]
    list4 = list_url[num3:len(list_url)]

    # 开启4个线程
    th1 = threading.Thread(target=get_img1)
    th2 = threading.Thread(target=get_img2)
    th3 = threading.Thread(target=get_img3)
    th4 = threading.Thread(target=get_img4)

    th1.start()
    th2.start()
    th3.start()
    th4.start()

    th1.join()
    th2.join()
    th3.join()
    th4.join()

    end_time = time.time()
    print(f'用时{end_time - start_time}秒')

    if fail_url_list:
        print(f'{len(fail_url_list)}张图片下载失败\n{fail_url_list}')
    print(f'{len(success_url)}张图片下载成功\n{success_url}')
    input('回车以结束程序')