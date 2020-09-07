import asyncio, aiohttp, aiofiles, os
from time import time, sleep, strftime, localtime
from bs4 import BeautifulSoup
from threading import Thread

from PySide2.QtWidgets import QApplication
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import Signal,QObject

class MySignals(QObject):
    text_print = Signal(str)
    update = Signal(int)

class GUI():
    def __init__(self):
        self.window = QUiLoader().load('wallhaven.ui')
        self.window.pb.setRange(0,10)
        self.header = {'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'}
        self.window.rb1.clicked.connect(self.d1)
        self.window.rb2.clicked.connect(self.d3)
        self.window.rb3.clicked.connect(self.d7)
        self.window.rb4.clicked.connect(self.m1)
        self.window.rb5.clicked.connect(self.m3)
        self.window.rb6.clicked.connect(self.m6)
        self.window.bt1.clicked.connect(self.spider)
        self.window.bt2.clicked.connect(self.download)
        self.ms = MySignals()
        self.ms.text_print.connect(self.print_to_GUI)
        self.ms.update.connect(self.update_pbar)

    def print_to_GUI(self, text):
        self.window.pte.appendPlainText(str(text))
    
    def update_pbar(self, i):
        self.window.pb.setValue(i)

    def d1(self):
        self.date = '1d'
    def d3(self):
        self.date = '3d'
    def d7(self):
        self.date = '7d'
    def m1(self):
        self.date = '1M'
    def m3(self):
        self.date = '3M'
    def m6(self):
        self.date = '6M'

    def spider(self):
        self.page_list = list(range(1, int(self.window.text.text()) + 1))
        self.window.pb.setRange(1, int(self.window.text.text()) + 1)
        with open('all url.txt', 'r+') as f:
            self.all_list = f.read().splitlines()
            f.write(strftime('%Y-%m-%d',localtime(time())) + '-' + self.date + '\n')
            self.ms.text_print.emit(f'已爬取{len(self.all_list)}张图片')

        async def login(session):
            '''登录'''
            self.ms.text_print.emit('开始登录...')
            login_index_url = 'https://wallhaven.cc/login'
            response = await session.get(login_index_url, headers=self.header)
            html = await response.text()
            bf = BeautifulSoup(html, 'lxml')
            hidden = bf.find_all('input', {'type':'hidden'})
            for i in hidden:
                _token = i['value']
            data = {
                '_token' : _token,
                'username': '', # 账号
                'password': ''  # 密码
            }
            login_url = 'https://wallhaven.cc/auth/login'
            response = await session.post(login_url, headers=self.header, data=data)
            if response.status == 200:
                self.ms.text_print.emit('登录成功')
            else:
                self.ms.text_print.emit(f'登录失败 HTTP:{response.status}')

        async def get_url(session):
            '''爬取排行榜'''
            for i in self.page_list:
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
                    full_url = 'https://w.wallhaven.cc/full/' + little_name + '/wallhaven-' + small_name + '.jpg' # 通过排行榜的链接url补全可以直接下载图片的url，默认图片是jpg格式
                    if full_url not in self.all_list:
                        async with aiofiles.open('all url.txt', 'a') as f:
                            await f.write(full_url + '\n')
                        async with aiofiles.open('url.txt', 'a') as e:
                            await e.write(full_url + '\n')
                self.ms.update.emit(i + 1)

        def create_txt():
            '''首次运行创建文本文件'''
            if not os.path.exists('url.txt'):
                f = open('url.txt', 'a')
                f.close()
            if not os.path.exists('all url.txt'):
                f = open('all url.txt', 'a')
                f.close()

        async def main():
            '''主程序'''
            create_txt()
            async with aiohttp.connector.TCPConnector(limit=300, force_close=True, enable_cleanup_closed=True, verify_ssl=False) as tc:
                async with aiohttp.ClientSession(connector=tc) as session:
                    await login(session)
                    await get_url(session)

        def run_main():
            start = time()
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(main())
                loop.close()
            except (aiohttp.client_exceptions.ClientConnectionError, asyncio.exceptions.TimeoutError) as e:
                self.ms.text_print.emit(e)
            self.ms.text_print.emit(f'用时{int((time()-start) // 60)}分{int((time()-start) % 60)}秒')
        
        t = Thread(target=run_main)
        t.start()

    def download(self):
        self.dir_name = strftime('%Y-%m-%d',localtime(time())) + '-' + self.date # 文件名
        self.dir_path = os.path.abspath('.') + os.sep + self.dir_name + os.sep # 路径

        #新建文件夹
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)

        #去除失败的和已下载的url
        files = []
        n = 0
        for file in os.listdir(self.dir_path):
            files.append(file)
        # 即将下载的url
        with open("url.txt", "r") as f:
            url_list = f.read().splitlines()

        # 失败的url
        with open("fail.txt", "r") as f:
            url_fail = f.read().splitlines()

        with open("url.txt", "r+") as f:
            url_all = f.read()
            for i in url_list:
                endwith = i.split('/')[-1]
                if endwith in files:
                    url_all = url_all.replace(f"{i}\n", "")
                if endwith in url_fail:
                    url_all = url_all.replace(f"{i}\n", "")
            f.seek(0)
            f.truncate()
            f.write(url_all)

        with open('url.txt', 'r') as f:
            self.url_list = f.read().splitlines()
            self.ms.text_print.emit(f'开始下载{len(self.url_list)}张图片...')
            self.window.pb.setRange(0, len(self.url_list))
        self.n = 0

        async def change_fail(i):
            '''异步修改fail.txt'''
            async with aiofiles.open("fail.txt", "r+") as f:
                data = await f.read()
                await f.seek(0)
                await f.truncate()
                await f.write(data.replace(i+"\n", ""))

        def write_fail_url(i):
            '''保存失败url'''
            with open('fail.txt', 'a') as f:
                f.write(i + '\n')

        async def img_download(url, sem, session, fail=False):
            '''下载图片'''
            async with sem:
                name = url.split('/')[-1]
                filename = self.dir_path + name #拼装文件名
                response = await session.get(url, headers=self.header)
                if response.status != 200:
                    url = url.replace(".jpg",".png") # 如果404则把url中的jpg替换为png
                    filename = self.dir_path + name #拼装文件名
                    #flag = True
                    response = await session.get(url, headers=self.header) # 重新获取
                    if response.status != 200:
                        if not fail:
                            self.ms.text_print.emit(f"{name}失效，已移除")
                            write_fail_url(url)
                        return

                file_size = int(response.headers['content-length']) # 询问文件大小

                if os.path.exists(filename):
                    first_byte = os.path.getsize(filename) # 本地文件大小
                else:
                    first_byte = 0
                if first_byte >= file_size:
                    self.ms.text_print.emit(f'{name}已存在')
                    if fail:
                        self.fail_url_list.remove(url)
                    return
                headers = {
                    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
                    'Range': f'bytes={first_byte}-{file_size}'}
                try:
                    response = await session.get(url, headers=headers)
                    with open(filename, 'ab') as f:
                        while True:
                            chunk = await response.content.read(1024)
                            if not chunk:
                                break
                            f.write(chunk)
                    if fail:
                        change_fail(url) # 重新下载成功则从失败url中除去

                    if os.path.getsize(filename) < file_size: # 如果本地文件小于图片文件则加入重新下载
                        write_fail_url(url)

                    self.n += 1
                    self.ms.update.emit(self.n)
                except:
                    if not fail:
                        write_fail_url(url)
                    self.ms.text_print.emit(f'{name}下载失败')

        async def main():
            '''主程序'''
            async with aiohttp.connector.TCPConnector(limit=300, force_close=True, enable_cleanup_closed=True, verify_ssl=False) as tc:
                async with aiohttp.ClientSession(connector=tc) as session:
                    sem = asyncio.Semaphore(10) # 限制异步线程数为10个
                    tasks = [img_download(url, sem, session) for url in self.url_list]
                    await asyncio.gather(*tasks)
                    
                    for _ in range(3): # 尝试重新下载3次，避免死循环
                        with open("fail.txt", "r") as f:
                            self.fail_url_list = f.read().splitlines()
                        if self.fail_url_list:
                            self.ms.text_print.emit(f'{len(self.fail_url_list)}张图片下载失败\n开始重新下载')
                            tasks = [img_download(url, sem, session, fail=True) for url in self.fail_url_list]
                            await asyncio.gather(*tasks)
                        else:
                            break
                    self.ms.text_print.emit(f'程序执行完毕\n{self.n}张图片下载完成')

        def run_main():
            '''运行'''
            start = time()
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(main())
                loop.close()
            except (aiohttp.client_exceptions.ClientConnectionError, asyncio.exceptions.TimeoutError):
                run_main()
                return
            self.ms.text_print.emit(f'用时{int((time()-start) // 60)}分{int((time()-start) % 60)}秒')

        t = Thread(target=run_main)
        t.start()

if __name__ == "__main__":
    app = QApplication([])
    stats = GUI()
    stats.window.show()
    app.exec_()