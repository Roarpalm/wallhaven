#!/usr/bin/env python3
#-*-coding:utf-8-*-

from bs4 import BeautifulSoup
import asyncio, aiohttp, aiofiles, os, time

async def main():
    with open('fail.txt', 'r') as f:
        list_url = f.read().splitlines()

    print(f'开始下载{len(list_url)}张图片')
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in list_url:
            task = img_download(url, session)
            tasks.append(task)
        await asyncio.gather(*tasks)

    with open('fail.txt', 'w') as f:
        if fail_url_list:
            for i in fail_url_list:
                f.write(f'{i}\n')
    print(f'还有{len(fail_url_list)}张图片下载失败')



async def img_download(url, session):
    '''下载图片'''
    global fail_url_list, download
    #async with ten:
    name = url.split('/')
    filename = b + name[-1]
    print(f'开始下载：{name[-1]}')
    try:
        async with session.get(url, headers=headers) as response:
            async with aiofiles.open(filename, "wb") as f :
                img = await response.content.read()
                await f.write(img)
        download += 1
        print(f'第{download}张图片下载完成：{name[-1]}')
    except:
        print(f'下载失败：{name[-1]}')
        # 保存下载失败的url在fail_url_list
        fail_url_list.append(url)

if __name__ == "__main__":
    fail_url_list = []
    download = 0

    # 新建文件夹
    b = os.path.abspath('.') + '\\' + 'fail' +'\\'
    if not os.path.exists(b):
        os.makedirs(b)

    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'}

    # 开始计时
    start = time.time()

    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(main())
    loop.run_until_complete(future)
    print(f'用时{time.time()-start}')
    input('回车以结束程序...')