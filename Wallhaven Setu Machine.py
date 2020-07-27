import asyncio, aiohttp, aiofiles, os
from tqdm import tqdm
from time import time, sleep, strftime, localtime
from bs4 import BeautifulSoup
from threading import Thread

class Wallhaven():
    def __init__(self):
        self.header = {'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'}
        self.date = input("Which day's sexy img do you want: ")
        # please input 1d, 3d, 7d, 1M, 3M, 6M, 1Y
        self.page = input('How many pages do you want: ')
        # 24 imgs per page
        self.spider()
        self.download()

    def spider(self):
        self.page_list = list(range(1, int(self.page) + 1))
        with open('all url.txt', 'r+') as f:
            self.all_list = f.read().splitlines()
            f.write(strftime('%Y-%m-%d',localtime(time())) + '-' + self.date + '\n')
            print(f'You have downloaded {len(self.all_list)} imgs.')

        async def login(session):
            '''login'''
            print('Start login...')
            login_index_url = 'https://wallhaven.cc/login'
            response = await session.get(login_index_url, headers=self.header)
            html = await response.text()
            bf = BeautifulSoup(html, 'lxml')
            hidden = bf.find_all('input', {'type':'hidden'})
            for i in hidden:
                _token = i['value']
            data = {
                '_token' : _token,
                'username': '', # Your username
                'password': ''  # Your password
            }
            login_url = 'https://wallhaven.cc/auth/login'
            response = await session.post(login_url, headers=self.header, data=data)
            if response.status == 200:
                print('Login success')
            else:
                print(f'Login fail, HTTP:{response.status}')

        async def get_url(session):
            '''get leaderboard'''
            pbar = tqdm(self.page_list, ncols=85) # process bar
            for i in pbar:
                pbar.set_description(f'{i} page...')
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
                    full_url = 'https://w.wallhaven.cc/full/' + little_name + '/wallhaven-' + small_name + '.jpg' # get the full url
                    if full_url not in self.all_list:
                        async with aiofiles.open('all url.txt', 'a') as f:
                            await f.write(full_url + '\n')
                        async with aiofiles.open('url.txt', 'a') as e:
                            await e.write(full_url + '\n')

        def create_txt():
            '''creat txt'''
            if not os.path.exists('url.txt'):
                f = open('url.txt', 'a')
                f.close()
            if not os.path.exists('all url.txt'):
                f = open('all url.txt', 'a')
                f.close()

        async def main():
            '''main program'''
            create_txt()
            async with aiohttp.connector.TCPConnector(limit=300, force_close=True, enable_cleanup_closed=True, verify_ssl=False) as tc:
                async with aiohttp.ClientSession(connector=tc) as session:
                    await login(session)
                    await get_url(session)

        def run_main():
            '''auto running again when something wrong'''
            start = time()
            try:
                asyncio.run(main())
            except (aiohttp.client_exceptions.ClientConnectionError, asyncio.exceptions.TimeoutError):
                sleep(10)
                run_main()
            print(f'cost {int((time()-start) // 60)} min {int((time()-start) % 60)}second')
        
        run_main()

    def download(self):
        self.fail_url_list = []
        self.dir_name = strftime('%Y-%m-%d',localtime(time())) + '-' + self.date # name
        self.dir_path = os.path.abspath('.') + os.sep + self.dir_name + os.sep # path
        with open('url.txt', 'r') as f:
            self.url_list = f.read().splitlines()
            print(f'It is going to download {len(self.url_list)} imgs...')
        self.n = 0

        def new_dir():
            '''creat new dir'''
            if not os.path.exists(self.dir_path):
                os.makedirs(self.dir_path)
        
        async def img_download(url, sem, session, fail=False):
            '''download img'''
            async with sem:
                name = url.split('/')
                filename = self.dir_path + name[-1]
                response = await session.get(url, headers=self.header)
                try:
                    file_size = int(response.headers['content-length']) # ask size
                except:
                    url = url.replace("jpg", "png")
                else:
                    if os.path.exists(filename):
                        first_byte = os.path.getsize(filename)
                    else:
                        first_byte = 0
                    if first_byte >= file_size:
                        print(f'{name[-1]} is already')
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
                            with tqdm(total=file_size, initial=first_byte, unit='B', unit_scale=True, desc=name[-1], ncols=85) as pbar: # process bar
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
                            self.fail_url_list.remove(url) # delete url from fail_url_list
                        self.n += 1
                    except:
                        if not fail:
                            self.fail_url_list.append(url)
                        print(f'{name[-1]} fail to download')

        def write_fail_url():
            '''save fail url'''
            if self.fail_url_list:
                with open('fail.txt', 'a') as f:
                    for i in self.fail_url_list:
                        f.write(i + '\n')

        async def main():
            '''main program'''
            new_dir()
            async with aiohttp.connector.TCPConnector(limit=300, force_close=True, enable_cleanup_closed=True, verify_ssl=False) as tc:
                async with aiohttp.ClientSession(connector=tc) as session:
                    sem = asyncio.Semaphore(10)
                    tasks = [img_download(url, sem, session) for url in self.url_list]
                    await asyncio.gather(*tasks)
                    print(f'{len(self.fail_url_list)} imgs fail to download\nauto start downloading again...')
                    with open("url.txt","r+",) as f:
                        jpgs = f.read().splitlines()
                        for i in jpgs:
                            i = i.replace("jpg", "png")
                            self.fail_url_list.append(i)
                    for _ in range(3): # try to download again in 3 times
                        if self.fail_url_list:
                            tasks = [img_download(url, sem, session, fail=True) for url in self.fail_url_list]
                            await asyncio.gather(*tasks)
                        else:
                            break
                    write_fail_url()
                    print(f'Finish! \n{len(self.url_list) - len(self.fail_url_list)} imgs download success')

        def run_main():
            '''run'''
            start = time()
            try:
                asyncio.run(main())
            except (aiohttp.client_exceptions.ClientConnectionError, asyncio.exceptions.TimeoutError):
                run_main()
                return
            print(f'cost {int((time()-start) // 60)} min {int((time()-start) % 60)} second')

        run_main()

if __name__ == "__main__":
    Wallhaven()