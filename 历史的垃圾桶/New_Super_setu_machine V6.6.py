#!/usr/bin/env python3
#-*-coding:utf-8-*-

from tqdm import tqdm
from bs4 import BeautifulSoup
from time import time
import aiohttp, asyncio, os

async def login():
    '''登录'''
    print('开始登录...')
    # 请求登录页面，获取_token
    login_index_url = 'https://wallhaven.cc/login'
    async with aiohttp.connector.TCPConnector(limit=300, force_close=True, enable_cleanup_closed=True) as tc:
        async with aiohttp.ClientSession(connector=tc) as session:
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
                hello = await session.post(login_url, headers=headers, data=data)
                if hello.status == 200:
                    print('登录成功')
                else:
                    print('登录失败')

                # 网站限制，顺序执行
                await get_url(page, session)

                write_url()

                ten = asyncio.Semaphore(10)
                works = [img_download(url, session, ten) for url in good_url]
                await asyncio.gather(*works)
                print(f'{len(fail_url_list)}张图片下载失败')

                for _ in range(3):
                    if fail_url_list:
                        print('开始重新下载...')
                        tasks = [img_download(url, session, ten, fail=True) for url in fail_url_list]
                        await asyncio.gather(*tasks)
                    else:
                        break
                
                # 保存莫名失败的url到文本
                if fail_url_list:
                    with open('fail.txt', 'a') as f:
                        for i in fail_url_list:
                            f.write(i + '\n')
                print(f'{len(good_url) - len(fail_url_list)}张图片下载完成')



async def get_url(page, session):
    global list_url
    pbar = tqdm(page, ncols=85)
    for i in pbar:
        pbar.set_description(f'正在采集第{i}页')
        if i == 1:
            # 001代表NSFW 1y代表过去一年 1M代表过去一月 1w代表过去一周 1d代表过去一天 toplist
            url = 'https://wallhaven.cc/search?categories=111&purity=001&topRange=3d&sorting=toplist&order=desc&page'
        else:
            url = f'https://wallhaven.cc/search?categories=111&purity=001&topRange=3d&sorting=toplist&order=desc&page={i}'

        resp = await session.get(url, headers=headers)
        req = await resp.text()
        bf = BeautifulSoup(req, 'lxml')
        # 搜索所有figure
        targets_url = bf.find_all('figure')
        for each in targets_url:
            # 提取其中的href链接并转化为图片url
            page_url = each.a.get('href')
            small_name = page_url.split('/')[-1]
            little_name = small_name[0:2]
            full_url = 'https://w.wallhaven.cc/full/' + little_name + '/wallhaven-' + small_name + '.jpg'
            list_url.append(full_url)



async def img_download(url, session, ten, fail=False):
    '''下载图片'''
    global fail_url_list
    async with ten:
        name = url.split('/')
        filename = b + name[-1]
        async with session.get(url, headers=headers) as response:
            try:
                file_size = int(response.headers['content-length'])
            except Exception as e:
                print(f'{e}\n请手动打开{url}')
            else:
                if os.path.exists(filename):
                    # 读取文件大小
                    first_byte = os.path.getsize(filename)
                else:
                    first_byte = 0
                if first_byte >= file_size:
                    print(f'{name[-1]}已存在\n')
                    return file_size
                # 从断点继续下载
                headers_ = {
                    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
                    'Range': f'bytes={first_byte}-{file_size}'}
                try:
                    async with session.get(url, headers=headers_) as response:
                        with(open(filename, 'ab')) as f:
                            with tqdm(total=file_size, initial=first_byte, unit='B', unit_scale=True, desc=f'{name[-1]} {round(file_size/1024,2)}KB', ncols=85) as pbar:
                                while True:
                                    chunk = await response.content.read(1024)
                                    if not chunk:
                                        break
                                    f.write(chunk)
                                    pbar.update(len(chunk))
                    if fail:
                        fail_url_list.remove(url)
                except Exception as e:
                    if fail:
                        print(f'重新下载失败：{name[-1]}\n原因：{e}')
                    else:
                        print(f'下载失败：{name[-1]}\n原因：{e}')
                        # 保存下载失败的url在fail_url_list
                        fail_url_list.append(url)



def write_url():
    '''保存已爬url'''
    global good_url
    # 读取已爬的url，如果重复，则删除
    with open('all-url.txt', 'r') as f:
        all_list = f.read().splitlines()
        print(f'已爬取{len(all_list)}张图片')
        for i in list_url:
            if i not in all_list:
                good_url.append(i)
        print(f'删除{len(list_url)-len(good_url)}个重复url')

    # 将新爬的url添加到列表末尾并写入
    if good_url:
        with open('all-url.txt', 'a') as f:
            for i in good_url:
                f.write(i + '\n')
            print(f'新增{len(good_url)}个url到文本')
    else:
        print('没有新图')

if __name__ == "__main__":
    list_url = []
    fail_url_list = []
    good_url = []

    # 在此更改采集的页数
    page = list(range(1,2))
    page_name = f'{page[0]}-{page[-1]}'

    # 新建文件夹
    b = os.path.abspath('.') + '\\' + page_name +'\\'
    if not os.path.exists(b):
        os.makedirs(b)

    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'}

    # 开始计时
    start = time()

    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(login())
    loop.run_until_complete(future)

    print(f'用时{int((time()-start) // 60)}分{int((time()-start) % 60)}秒')
    input('回车以结束程序...')