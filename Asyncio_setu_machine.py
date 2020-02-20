#!/usr/bin/env python3
#-*-coding:utf-8-*-

from bs4 import BeautifulSoup
import aiohttp, asyncio, aiofiles, os, time

async def login():
    '''登录'''
    print('开始登录...')
    # 请求登录页面，获取_token
    login_index_url = 'https://wallhaven.cc/login'
    async with aiohttp.ClientSession() as session:
        async with session.get(login_index_url, headers=headers) as response:
            html = await response.text()
            bf_1 = BeautifulSoup(html, 'lxml')
            hidden = bf_1.find_all('input', {'type':'hidden'})
            for i in hidden:
                _token = i['value']

            data = {
                '_token' : _token,
                'username': '', # 填入账号
                'password': ''  # 填入密码
            }

            # 请求登录的url
            login_url = 'https://wallhaven.cc/auth/login'
            await session.post(login_url, headers=headers, data=data)
            print('登录成功')

            # 限制同时进行的协程只有1个，多次尝试感觉是网站的问题，同时请求网页的次数越多，获取失败的概率越大
            one = asyncio.Semaphore(1)
            tasks = []
            for i in page:
                task = get_url(i, session, one)
                tasks.append(task)
            await asyncio.gather(*tasks)

            write_url()
            print(f'开始解析{len(list_url)}个url')

            new_tasks = []
            for i in list_url:
                new_task = get_img(i, session, one)
                new_tasks.append(new_task)
            await asyncio.gather(*new_tasks)
            print('解析完成')

            # 限制同时下载的协程只有20个
            ten = asyncio.Semaphore(20)
            works = []
            for i in ture_url:
                work = img_download(i, session, ten)
                works.append(work)
            await asyncio.gather(*works)
            print(f'{len(fail_url_list)}张图片下载失败')

            write_fail_url()
            print(f'{len(ture_url) - len(fail_url_list)}张图片下载完成')



async def get_url(i, session, one):
    global list_url
    async with one:
        print(f'正在采集第{i}页')
        if i == 1:
            # 001代表NSFW 1y代表过去一年 1M代表过去一月 1w代表过去一周 1d代表过去一天 toplist
            url = 'https://wallhaven.cc/search?categories=111&purity=001&topRange=1w&sorting=toplist&order=desc&page'
        else:
            url = f'https://wallhaven.cc/search?categories=111&purity=001&topRange=1w&sorting=toplist&order=desc&page={i}'

        resp = await session.get(url, headers=headers)
        req = await resp.text()
        bf = BeautifulSoup(req, 'lxml')
        # 搜索所有figure
        targets_url = bf.find_all('figure')
        for each in targets_url:
            # 提取其中的href链接并保存在list_url
            list_url.append(each.a.get('href'))
        print(f'第{i}页采集完成')



async def get_img(url, session, one):
    '''解析网页获取图片url'''
    global ture_url
    # 这一步是最耗时的，但又偏偏不能并行
    async with one:
        print(f'解析中...({len(ture_url)}/{len(list_url)})', end='\r')
        async with session.get(url, headers=headers) as response:
            img_html = await response.read()
            img_bf_1 = BeautifulSoup(img_html, 'lxml')
            # 搜索所有wallpaper
            div = img_bf_1.find_all('img', {'id':'wallpaper'})
            for urls in div:
                img_url = urls['src']
                # 保存在ture_url
                ture_url.append(img_url)



async def img_download(url, session, ten):
    '''下载图片'''
    global fail_url_list, download
    async with ten:
        name = url.split('/')
        filename = b + name[-1]
        print(f'开始下载：{name[-1]}')
        try:
            async with session.get(url, headers=headers) as response:
                async with aiofiles.open(filename, "wb") as f :
                    while True:
                        # 分步下载，哪怕下载失败也能看到大概一半的图片
                        chunk = await response.content.read(1024)
                        if not chunk:
                            break
                        await f.write(chunk)
            download += 1
            print(f'第{download}张图片下载完成：{name[-1]}')
            await asyncio.sleep(0.5)
        except:
            print(f'下载失败：{name[-1]}')
            # 保存下载失败的url在fail_url_list
            fail_url_list.append(url)



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
        print(f'新增{len(fail_url_list)}个失败url到文本')

if __name__ == "__main__":
    list_url = []
    ture_url = []
    fail_url_list = []
    download = 0

    # 在此更改采集的页数
    page = list(range(1, 31))
    page_name = f'{page[0]}-{page[-1]}'

    # 新建文件夹
    b = os.path.abspath('.') + '\\' + page_name +'\\'
    if not os.path.exists(b):
        os.makedirs(b)

    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'}

    # 开始计时
    start = time.time()

    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(login())
    loop.run_until_complete(future)
    print(f'用时{time.time()-start}')
    input('回车以结束程序...')