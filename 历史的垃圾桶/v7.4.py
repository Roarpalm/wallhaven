# utf-8
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
            self.ms.text_print.emit(f'����ȡ{len(self.all_list)}��ͼƬ')

        async def login(session):
            '''��¼'''
            self.ms.text_print.emit('��ʼ��¼...')
            login_index_url = 'https://wallhaven.cc/login'
            response = await session.get(login_index_url, headers=self.header)
            html = await response.text()
            bf = BeautifulSoup(html, 'lxml')
            hidden = bf.find_all('input', {'type':'hidden'})
            for i in hidden:
                _token = i['value']
            data = {
                '_token' : _token,
                'username': 'roarpalm', # �˺�
                'password': 'qweasdzxc'  # ����
            }
            login_url = 'https://wallhaven.cc/auth/login'
            response = await session.post(login_url, headers=self.header, data=data)
            if response.status == 200:
                self.ms.text_print.emit('��¼�ɹ�')
            else:
                self.ms.text_print.emit(f'��¼ʧ�� HTTP:{response.status}')

        async def get_url(session):
            '''��ȡ���а�'''
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
                    full_url = 'https://w.wallhaven.cc/full/' + little_name + '/wallhaven-' + small_name + '.jpg' # ͨ�����а������url��ȫ����ֱ������ͼƬ��url��Ĭ��ͼƬ��jpg��ʽ
                    if full_url not in self.all_list:
                        async with aiofiles.open('all url.txt', 'a') as f:
                            await f.write(full_url + '\n')
                        async with aiofiles.open('url.txt', 'a') as e:
                            await e.write(full_url + '\n')
                self.ms.update.emit(i + 1)

        def create_txt():
            '''�״����д����ı��ļ�'''
            if not os.path.exists('url.txt'):
                f = open('url.txt', 'a')
                f.close()
            if not os.path.exists('all url.txt'):
                f = open('all url.txt', 'a')
                f.close()

        async def main():
            '''������'''
            create_txt()
            async with aiohttp.connector.TCPConnector(limit=300, force_close=True, enable_cleanup_closed=True, verify_ssl=False) as tc:
                async with aiohttp.ClientSession(connector=tc) as session:
                    await login(session)
                    await get_url(session)

        def run_main():
            start = time()
            try:
                asyncio.run(main())
            except (aiohttp.client_exceptions.ClientConnectionError, asyncio.exceptions.TimeoutError):
                sleep(10)
                run_main()
            self.ms.text_print.emit(f'��ʱ{int((time()-start) // 60)}��{int((time()-start) % 60)}��')
        
        t = Thread(target=run_main)
        t.start()

    def download(self):
        self.fail_url_list = [] # ����ʧ�ܵ�url
        self.dir_name = strftime('%Y-%m-%d',localtime(time())) + '-' + self.date # �ļ���
        self.dir_path = os.path.abspath('.') + os.sep + self.dir_name + os.sep # ·��
        with open('url.txt', 'r') as f:
            self.url_list = f.read().splitlines()
            self.ms.text_print.emit(f'������ʼ����{len(self.url_list)}��ͼƬ...')
            self.window.pb.setRange(0, len(self.url_list))
        self.n = 0

        def new_dir():
            '''�½��ļ���'''
            if not os.path.exists(self.dir_path):
                os.makedirs(self.dir_path)
        
        async def img_download(url, sem, session, fail=False):
            '''����ͼƬ'''
            async with sem:
                name = url.split('/')
                filename = self.dir_path + name[-1]
                response = await session.get(url, headers=self.header)
                try:
                    file_size = int(response.headers['content-length']) # ѯ���ļ���С
                except:
                    return
                else:
                    if os.path.exists(filename):
                        first_byte = os.path.getsize(filename) # �����ļ���С
                    else:
                        first_byte = 0
                    if first_byte >= file_size:
                        self.ms.text_print.emit(f'{name[-1]}�Ѵ���')
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
                            while True:
                                chunk = await response.content.read(1024)
                                if not chunk:
                                    break
                                f.write(chunk)
                        async with aiofiles.open('url.txt', 'r+') as f:
                            data = await f.read()
                            await f.seek(0)
                            await f.truncate()
                            await f.write(data.replace(f'{url}\n', ''))
                        if fail:
                            self.fail_url_list.remove(url) # �������سɹ����ʧ��url�г�ȥ
                        self.n += 1
                        self.ms.update.emit(self.n)
                    except:
                        if not fail:
                            self.fail_url_list.append(url)
                        self.ms.text_print.emit(f'{name[-1]}����ʧ��')

        def write_fail_url():
            '''����ʧ��url'''
            if self.fail_url_list:
                with open('fail.txt', 'a') as f:
                    for i in self.fail_url_list:
                        f.write(i + '\n')

        async def main():
            '''������'''
            new_dir()
            async with aiohttp.connector.TCPConnector(limit=300, force_close=True, enable_cleanup_closed=True, verify_ssl=False) as tc:
                async with aiohttp.ClientSession(connector=tc) as session:
                    sem = asyncio.Semaphore(10)
                    tasks = [img_download(url, sem, session) for url in self.url_list]
                    await asyncio.gather(*tasks)
                    self.ms.text_print.emit(f'{len(self.fail_url_list)}��ͼƬ����ʧ��\n��ʼ��������')
                    for _ in range(3): # ������������3�Σ�������ѭ��
                        if self.fail_url_list:
                            tasks = [img_download(url, sem, session, fail=True) for url in self.fail_url_list]
                            await asyncio.gather(*tasks)
                        else:
                            break
                    write_fail_url()
                    self.ms.text_print.emit(f'����ִ�����\n{len(self.url_list) - len(self.fail_url_list)}��ͼƬ�������')

        def run_main():
            '''����'''
            start = time()
            try:
                asyncio.run(main())
            except (aiohttp.client_exceptions.ClientConnectionError, asyncio.exceptions.TimeoutError):
                run_main()
                return
            self.ms.text_print.emit(f'��ʱ{int((time()-start) // 60)}��{int((time()-start) % 60)}��')

        t = Thread(target=run_main)
        t.start()

if __name__ == "__main__":
    app = QApplication([])
    stats = GUI()
    stats.window.show()
    app.exec_()