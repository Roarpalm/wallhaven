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

        def get_all_list():
            with open('all url.txt', 'r+') as f:
                all_list = f.read().splitlines()
                f.write(strftime('%Y-%m-%d',localtime(time())) + '-' + self.date + '\n')
                self.ms.text_print.emit(f'已爬取{len(all_list)}张图片')
            return all_list

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
                return True
            else:
                return False
            
        def create_txt():
            '''首次运行创建文本文件'''
            if not os.path.exists('url.txt'):
                f = open('url.txt', 'a')
                f.close()
            if not os.path.exists('all url.txt'):
                f = open('all url.txt', 'a')
                f.close()

        async def get_url(session):
            '''爬取排行榜'''
            if not await login(session):
                self.ms.text_print.emit(f'登录失败 HTTP:{response.status}')
                return
            else:
                self.ms.text_print.emit('登录成功')
                all_list = get_all_list()
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
                    #只保存图片编号
                    if small_name not in all_list:
                        async with aiofiles.open('all url.txt', 'a') as f:
                            await f.write(small_name + '\n')
                        async with aiofiles.open('url.txt', 'a') as e:
                            await e.write(small_name + '\n')
                self.ms.update.emit(i + 1)

        async def main():
            '''主程序'''
            create_txt()
            async with aiohttp.connector.TCPConnector(limit=300, force_close=True, enable_cleanup_closed=True, verify_ssl=False) as tc:
                async with aiohttp.ClientSession(connector=tc) as session:
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
        self.n = 0
        def create_new_dir():
            '''新建文件夹'''
            if not os.path.exists(self.dir_path):
                os.makedirs(self.dir_path)

        def get_url_list(file):
            '''从文件读取url'''
            with open(file, 'r') as f:
                url_list = f.read().splitlines()
            return url_list

        async def check_url(session, url, small_name):
            '''验证url'''
            response = await session.get(url, headers=self.header)
            if response.status != 200:
                if url.endswith("jpg"):
                    self.ms.text_print.emit(small_name + " HTTP:" + str(response.status))
                return False
            return response

        def get_full_url(small_name):
            '''拼接完整的url'''
            little_name = small_name[0:2]
            return "https://w.wallhaven.cc/full/" + little_name + "/wallhaven-" + small_name

        def write_fail_url(i):
            '''保存失败url'''
            with open('fail.txt', 'a') as f:
                f.write(i + '\n')

        async def change_txt(file, url):
            '''异步修改txt'''
            async with aiofiles.open(file, "r+") as f:
                data = await f.read()
                await f.seek(0)
                await f.truncate()
                await f.write(data.replace(url + "\n", ""))

        async def img_download(small_name, sem, session, fail=False):
            '''下载图片'''
            async with sem:
                url = get_full_url(small_name) + ".jpg"
                response = await check_url(session, url, small_name)
                if not response:
                    url = get_full_url(small_name) + ".png"
                    response = await check_url(session, url, small_name)
                    if not response:
                        self.ms.text_print.emit(f"{small_name}失效，已移除")
                        if not fail:
                            write_fail_url(small_name)
                        return

                name = url.split('/')[-1]
                filename = self.dir_path + name #拼装文件名

                file_size = int(response.headers['content-length']) # 询问文件大小

                #如果本地文件已存在，则判断大小，重新赋值headers
                if os.path.exists(filename):
                    first_byte = os.path.getsize(filename) # 本地文件大小
                    if first_byte >= file_size:
                        self.ms.text_print.emit(f'{small_name}已存在')
                        await change_txt("url.txt", small_name)
                        return
                    headers = {
                        'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
                        'Range': f'bytes={first_byte}-{file_size}'}
                    response = await session.get(url, headers=headers)
                try:
                    with open(filename, 'ab') as f:
                        while True:
                            chunk = await response.content.read(1024)
                            if not chunk:
                                break
                            f.write(chunk)
                except:
                    if not fail:
                        write_fail_url(small_name)
                    self.ms.text_print.emit(f'{small_name}下载失败')
                    return

                
                if fail:
                    await change_txt("fail.txt", small_name) # 重新下载成功则从失败url中除去
                else:
                    if os.path.getsize(filename) < file_size: # 如果本地文件小于图片文件则加入重新下载
                        write_fail_url(small_name)
                    else:
                        #到这步就是下载成功了
                        await change_txt("url.txt", small_name)
                        self.n += 1
                        self.ms.update.emit(self.n)

        async def main():
            '''主程序'''
            async with aiohttp.connector.TCPConnector(limit=300, force_close=True, enable_cleanup_closed=True, verify_ssl=False) as tc:
                async with aiohttp.ClientSession(connector=tc) as session:
                    create_new_dir()

                    sem = asyncio.Semaphore(10) # 限制异步线程数为10个
                    url_list = get_url_list("url.txt")
                    self.ms.text_print.emit(f'开始下载{len(url_list)}张图片...')
                    self.window.pb.setRange(0, len(url_list))

                    tasks = [img_download(url, sem, session) for url in url_list]
                    await asyncio.gather(*tasks)

                    #重新下载失败的url
                    fail_url = get_url_list("fail.txt")
                    if len(fail_url) > 0:
                        self.ms.text_print.emit(f'{len(fail_url)}张图片下载失败\n开始重新下载')
                        tasks = [img_download(url, sem, session, fail=True) for url in fail_url]
                        await asyncio.gather(*tasks)

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