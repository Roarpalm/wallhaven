#!/usr/bin/env python3
#-*-coding:utf-8-*-

from tqdm import tqdm
from bs4 import BeautifulSoup
from time import time
import aiohttp, asyncio, os

class Wallhaven():
    def __init__(self):
        self.url_list = [] # 爬取的url
        self.fail_url_list = [] # 下载失败的url
        self.good_url_list = [] # 去重后的url
        self.n = int(input('你想看几页色图：'))
        self.num = ''
        self.date = ''
        self.page_list = list(range(1, self.n + 1)) # 爬取的页数
        self.dir_name = f'{self.page_list[0]}-{self.page_list[-1]}' # 文件名
        self.header = {'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'}
        self.dir_path = os.path.abspath('.') + os.sep + self.dir_name + os.sep # 路径
        self.run() # 自动运行

    async def main(self):
        '''主程序'''
        self.input_date()
        async with aiohttp.connector.TCPConnector(limit=300, force_close=True, enable_cleanup_closed=True) as tc:
            async with aiohttp.ClientSession(connector=tc) as session:
                await self.login(session)

                await self.get_url(self.page_list, session)

                self.check_txt()

                self.write_url()

                self.new_dir()

                ten = asyncio.Semaphore(10) # 限制并行10个下载协程
                tasks = [self.download(url, session, ten) for url in self.good_url_list]
                await asyncio.gather(*tasks)
                print(f'{len(self.fail_url_list)}张图片下载失败\n开始重新下载')

                for _ in range(3): # 尝试重新下载3次，避免死循环
                    if self.fail_url_list:
                        tasks = [self.download(url, session, ten, fail=True) for url in self.fail_url_list]
                        await asyncio.gather(*tasks)
                    else:
                        break

                self.write_fail_url()
                print(f'程序执行完毕\n{len(self.good_url_list) - len(self.fail_url_list)}张图片下载完成')



    def input_date(self):
        self.num = input('年度榜请输入 1\n半年榜请输入 2\n三月榜请输入 3\n月榜请输入   4\n周榜请输入   5\n三天榜请输入 6\n你想看哪个榜：')
        if self.num == '1':
            self.date = '1Y'
        elif self.num == '2':
            self.date = '6M'
        elif self.num == '3':
            self.date = '3M'
        elif self.num == '4':
            self.date = '1M'
        elif self.num == '5':
            self.date = '7d'
        elif self.num == '6':
            self.date = '3d'
        else:
            print('\n请输入正确对应的数字\n')
            self.input_date()



    async def login(self, session):
        '''登录'''
        print('开始登录...')
        login_index_url = 'https://wallhaven.cc/login'
        response = await session.get(login_index_url, headers=self.header)
        html = await response.text()
        bf = BeautifulSoup(html, 'lxml')
        hidden = bf.find_all('input', {'type':'hidden'})
        for i in hidden:
            _token = i['value']
        data = {
            '_token' : _token,
            'username': input('请输入账号：'), # 填入账号
            'password': input('请输入密码：')  # 填入密码
        }
        login_url = 'https://wallhaven.cc/auth/login'
        response = await session.post(login_url, headers=self.header, data=data)
        if response.status == 200:
            print('登录成功')
        else:
            print(f'登录失败 HTTP:{response.status}')



    async def get_url(self, page_list, session):
        '''爬取排行榜'''
        pbar = tqdm(page_list, ncols=85) # 进度条
        for i in pbar:
            pbar.set_description(f'正在采集第{i}页')
            if i == 1:
                url = f'https://wallhaven.cc/search?categories=111&purity=001&topRange={self.date}&sorting=toplist&order=desc&page'
            else:
                url = f'https://wallhaven.cc/search?categories=111&purity=001&topRange={self.date}&sorting=toplist&order=desc&page={i}'
            response = await session.get(url, headers=self.header)
            html = await response.text()
            bf = BeautifulSoup(html, 'lxml')
            targets_url = bf.find_all('figure')
            for each in targets_url:
                page_url = each.a.get('href')
                small_name = page_url.split('/')[-1]
                little_name = small_name[0:2]
                full_url = 'https://w.wallhaven.cc/full/' + little_name + '/wallhaven-' + small_name + '.jpg' # 通过排行榜的链接url补全可以直接下载图片的url
                self.url_list.append(full_url)



    def check_txt(self):
        if not os.path.exists('all-url.txt'):
            with open('all-url.txt', 'w'):
                pass



    def write_url(self):
        '''保存已爬url'''
        with open('all-url.txt', 'r') as f:
            all_list = f.read().splitlines()
            print(f'已爬取{len(all_list)}张图片')
            for i in self.url_list:
                if i not in all_list:
                    self.good_url_list.append(i)
            print(f'删除{len(self.url_list)-len(self.good_url_list)}个重复url')

        if self.good_url_list:
            with open('all-url.txt', 'a') as f:
                for i in self.good_url_list:
                    f.write(i + '\n')
                print(f'新增{len(self.good_url_list)}个url到文本')
        else:
            print('没有新图')



    def new_dir(self):
        '''新建文件夹'''
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)



    async def download(self, url, session, ten, fail=False):
        '''下载图片'''
        async with ten:
            name = url.split('/')
            filename = self.dir_path + name[-1]
            response = await session.get(url, headers=self.header)
            try:
                file_size = int(response.headers['content-length']) # 询问文件大小
            except:
                if not fail:
                    self.fail_url_list.append(url) # 有些图片的header里没有content-length会出现异常
                return
            else:
                if os.path.exists(filename):
                    first_byte = os.path.getsize(filename) # 本地文件大小
                else:
                    first_byte = 0
                if first_byte >= file_size:
                    print(f'{name[-1]}已存在')
                    return
                headers = {
                    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
                    'Range': f'bytes={first_byte}-{file_size}'}
                try:
                    response = await session.get(url, headers=headers)
                    with open(filename, 'ab') as f:
                        with tqdm(total=file_size, initial=first_byte, unit='B', unit_scale=True, desc=f'{name[-1]} {round(file_size/1024,2)}KB', ncols=85) as pbar: # 进度条
                            while True:
                                chunk = await response.content.read(1024)
                                if not chunk:
                                    break
                                f.write(chunk)
                                pbar.update(len(chunk))
                    if fail:
                        self.fail_url_list.remove(url) # 重新下载成功则从失败url中除去
                except:
                    print(f'下载失败：{name[-1]}')
                    if not fail:
                        self.fail_url_list.append(url)



    def write_fail_url(self):
        '''保存失败url'''
        if self.fail_url_list:
            with open('fail.txt', 'a') as f:
                for i in self.fail_url_list:
                    f.write(i + '\n')



    def run(self):
        start = time()
        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(self.main())
        loop.run_until_complete(future)
        print(f'用时{int((time()-start) // 60)}分{int((time()-start) % 60)}秒')


if __name__ == "__main__":
    print('-'*20,'欢迎使用Wallhaven色图机 V6.7','-'*20)
    print('-'*26,'作者：Roarpalm','-'*28,) 
    print('-'*10,'项目地址：https://github.com/Roarpalm/wallhaven', '-'*11)
    print('\n')

    Wallhaven()