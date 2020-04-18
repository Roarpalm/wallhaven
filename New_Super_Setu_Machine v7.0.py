import tkinter as tk
import tkinter.messagebox
import asyncio, aiohttp, aiofiles, os, threading
from time import time, sleep, strftime, localtime
from lxml import etree
from tqdm import tqdm
from bs4 import BeautifulSoup

header = {'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'}

class Spider():
    def __init__(self):
        b1['state'] = 'disabled'
        self.page_list = list(range(1, int(e1.get()) + 1)) # 爬取的页数
        self.date = e2.get() # 爬取的榜单
        with open('all url.txt', 'r+') as f:
            f.write(strftime('%Y-%m-%d',localtime(time())) + e2.get() + '\n')
            self.all_list = f.read().splitlines()
            print(f'已爬取{len(self.all_list)}张图片')
        self.run_main()
        b1['state'] = 'normal'
        
    async def login(self, session):
        '''登录'''
        print('开始登录...')
        login_index_url = 'https://wallhaven.cc/login'
        response = await session.get(login_index_url, headers=header)
        html = await response.text()
        bf = BeautifulSoup(html, 'lxml')
        hidden = bf.find_all('input', {'type':'hidden'})
        for i in hidden:
            _token = i['value']
        data = {
            '_token' : _token,
            'username': 'roarpalm', # 账号
            'password': 'qweasdzxc'  # 密码
        }
        login_url = 'https://wallhaven.cc/auth/login'
        response = await session.post(login_url, headers=header, data=data)
        if response.status == 200:
            print('登录成功')
        else:
            print(f'登录失败 HTTP:{response.status}')



    async def get_url(self, session):
        '''爬取排行榜'''
        pbar = tqdm(self.page_list, ncols=85) # 进度条
        for i in pbar:
            pbar.set_description(f'正在采集第{i}页')
            if i == 1:
                url = f'https://wallhaven.cc/search?categories=111&purity=001&topRange={self.date}&sorting=toplist&order=desc&page'
            else:
                url = f'https://wallhaven.cc/search?categories=111&purity=001&topRange={self.date}&sorting=toplist&order=desc&page={i}'
            response = await session.get(url, headers=header)
            html = await response.text()
            bf = BeautifulSoup(html, 'lxml')
            targets_url = bf.find_all('figure')
            for each in targets_url:
                page_url = each.a.get('href')
                small_name = page_url.split('/')[-1]
                little_name = small_name[0:2]
                full_url = 'https://w.wallhaven.cc/full/' + little_name + '/wallhaven-' + small_name + '.jpg' # 通过排行榜的链接url补全可以直接下载图片的url
                if full_url not in self.all_list:
                    async with aiofiles.open('all url.txt', 'a') as f:
                        await f.write(full_url + '\n')
                    async with aiofiles.open('url.txt', 'a') as e:
                        await e.write(full_url + '\n')




    def create_txt(self):
        '''首次运行创建文本文件'''
        if not os.path.exists('url.txt'):
            f = open('url.txt', 'a')
            f.close()
        if not os.path.exists('all url.txt'):
            f = open('all url.txt', 'a')
            f.close()



    async def main(self):
        '''主程序'''
        self.create_txt()
        async with aiohttp.connector.TCPConnector(limit=300, force_close=True, enable_cleanup_closed=True, verify_ssl=False) as tc:
            async with aiohttp.ClientSession(connector=tc) as session:
                await self.login(session)
                await self.get_url(session)  



    def run_main(self):
        '''运行'''
        start = time()
        try:
            asyncio.run(self.main())
        except (aiohttp.client_exceptions.ClientConnectionError, asyncio.exceptions.TimeoutError):
            sleep(10)
            self.run_main()
        print(f'用时{int((time()-start) // 60)}分{int((time()-start) % 60)}秒')
        tkinter.messagebox.showinfo(title='Hi!', message='爬取完成')



class Download():
    def __init__(self):
        b2['state'] = 'disabled'
        self.fail_url_list = [] # 下载失败的url
        self.dir_name = strftime('%Y-%m-%d',localtime(time())) + e2.get() # 文件名
        self.dir_path = os.path.abspath('.') + os.sep + self.dir_name + os.sep # 路径
        with open('url.txt', 'r') as f:
            self.url_list = f.read().splitlines()
            print(f'即将开始下载{len(self.url_list)}张图片...')
        self.run_main()
        b2['state'] = 'normal'

    def new_dir(self):
        '''新建文件夹'''
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)

    async def img_download(self, url, sem, session, fail=False):
        '''下载图片'''
        async with sem:
            name = url.split('/')
            filename = self.dir_path + name[-1]
            response = await session.get(url, headers=header)
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
                    if fail:
                        self.fail_url_list.remove(url)
                    else:
                        async with aiofiles.open('url.txt', 'r+') as f:
                            data = await f.read()
                            await f.seek(0)
                            await f.truncate()
                            await f.write(data.replace(f'{url}\n', ''))
                    return
                headers = {
                    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
                    'Range': f'bytes={first_byte}-{file_size}'}
                try:
                    response = await session.get(url, headers=headers)
                    with open(filename, 'ab') as f:
                        with tqdm(total=file_size, initial=first_byte, unit='B', unit_scale=True, desc=name[-1], ncols=85) as pbar: # 进度条
                            while True:
                                chunk = await response.content.read(1024)
                                if not chunk:
                                    break
                                f.write(chunk)
                                pbar.update(len(chunk))
                    async with aiofiles.open('url.txt', 'r+') as f:
                        data = await f.read()
                        await f.seek(0)
                        await f.truncate()
                        await f.write(data.replace(f'{url}\n', ''))
                    if fail:
                        self.fail_url_list.remove(url) # 重新下载成功则从失败url中除去
                except:
                    if not fail:
                        self.fail_url_list.append(url)



    def write_fail_url(self):
        '''保存失败url'''
        if self.fail_url_list:
            with open('fail.txt', 'a') as f:
                for i in self.fail_url_list:
                    f.write(i + '\n')

    

    async def main(self):
        '''主程序'''
        self.new_dir()
        async with aiohttp.connector.TCPConnector(limit=300, force_close=True, enable_cleanup_closed=True, verify_ssl=False) as tc:
            async with aiohttp.ClientSession(connector=tc) as session:
                sem = asyncio.Semaphore(10)
                tasks = [self.img_download(url, sem, session) for url in self.url_list]
                await asyncio.gather(*tasks)
                print(f'{len(self.fail_url_list)}张图片下载失败\n开始重新下载')
                for _ in range(3): # 尝试重新下载3次，避免死循环
                    if self.fail_url_list:
                        tasks = [self.img_download(url, sem, session, fail=True) for url in self.fail_url_list]
                        await asyncio.gather(*tasks)
                    else:
                        break
                self.write_fail_url()
                print(f'程序执行完毕\n{len(self.url_list) - len(self.fail_url_list)}张图片下载完成')



    def run_main(self):
        '''运行'''
        start = time()
        try:
            asyncio.run(self.main())
        except (aiohttp.client_exceptions.ClientConnectionError, asyncio.exceptions.TimeoutError):
            sleep(10)
            self.run_main()
        print(f'用时{int((time()-start) // 60)}分{int((time()-start) % 60)}秒')
        tkinter.messagebox.showinfo(title='Hi!', message='下载完成')



class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        global b1, b2, e1, e2
        self.title('Wallhaven') # 给窗口的可视化起名字
        self.geometry('400x130')  # 设定窗口的大小(长 * 宽)
        # 文字
        l1 = tk.Label(self, text='爬取页数：',font=('pingfang', 12))
        l1.place(x=80,y=30,anchor='s')
        l2 = tk.Label(self, text='榜单（1Y 1M 1d）：',font=('pingfang', 12))
        l2.place(x=290,y=30,anchor='s')
        # 输入框
        e1 = tk.Entry(self, show=None)
        e1.place(x=110,y=60,anchor='s')
        e2 = tk.Entry(self, show=None)
        e2.place(x=290,y=60,anchor='s')
        # 按钮
        b1 = tk.Button(self, text='爬取', font=('pingfang', 12), width=12, height=2, command=lambda :self.thread_it(Spider))
        b1.place(x=100,y=120,anchor='s')
        b2 = tk.Button(self, text='下载', font=('pingfang', 12), width=12, height=2, command=lambda :self.thread_it(Download))
        b2.place(x=290,y=120,anchor='s')

    @staticmethod
    def thread_it(func):
        '''打包进线程'''
        t = threading.Thread(target=func) 
        t.setDaemon(True)
        t.start()

if __name__ == "__main__":
    Application().mainloop()