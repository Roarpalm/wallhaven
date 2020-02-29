#!/usr/bin/env python3
#-*-coding:utf-8-*-

from bs4 import BeautifulSoup
import aiohttp, asyncio, os, time

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

                # 限制同时进行的协程只有1个，多次尝试感觉是网站的问题，同时请求网页的次数越多，获取失败的概率越大
                one = asyncio.Semaphore(1)
                tasks = [get_url(i, session, one) for i in page]
                await asyncio.gather(*tasks)

                write_url()

                ten = asyncio.Semaphore(10)
                works = [img_download(url, session, ten) for url in list_url]
                await asyncio.gather(*works)
                print(f'{len(fail_url_list)}张图片下载失败')

                while True:
                    if fail_url_list:
                        print('开始重新下载...')
                        tasks = [img_download(url, session, ten, fail=True) for url in fail_url_list]
                        await asyncio.gather(*tasks)
                    else:
                        break

                print(f'{len(list_url) - len(fail_url_list)}张图片下载完成')



async def get_url(i, session, one):
    global list_url
    async with one:
        print(f'正在采集第{i}页')
        if i == 1:
            # 001代表NSFW 1y代表过去一年 1M代表过去一月 1w代表过去一周 1d代表过去一天 toplist
            url = 'https://wallhaven.cc/search?categories=111&purity=001&topRange=1d&sorting=toplist&order=desc&page'
        else:
            url = f'https://wallhaven.cc/search?categories=111&purity=001&topRange=1d&sorting=toplist&order=desc&page={i}'

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
        print(f'第{i}页采集完成')



async def img_download(url, session, ten, fail=False):
    '''下载图片'''
    global fail_url_list
    async with ten:
        name = url.split('/')
        filename = b + name[-1]
        try:
            async with session.get(url, headers=headers) as response:
                file_size = int(response.headers['content-length'])
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
                async with session.get(url, headers=headers_) as response:
                    with(open(filename, 'ab')) as f:
                        progress = ProgressBar(name[-1], total=file_size, unit="KB", chunk_size=1024, run_status="正在下载", fin_status="下载完成")
                        while True:
                            chunk = await response.content.read(1024)
                            if not chunk:
                                break
                            f.write(chunk)
                            await progress.refresh(count=len(chunk))
            if fail:
                fail_url_list.remove(url)
        except Exception as e:
            print(f'下载失败：{name[-1]} {round(os.path.getsize(filename)/1024, 2)}kb/{round(file_size/1024, 2)}kb')
            print(e)
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
    with open('all-url.txt', 'a') as f:
        for i in list_url:
            f.write(f'{i}\n')
        print(f'新增{len(list_url)}个url到文本')



class ProgressBar(object):

    def __init__(
        self, title, count=0.0, run_status=None, fin_status=None, total=100.0, unit='', sep='/', chunk_size=1.0):
        super(ProgressBar, self).__init__()
        self.info = "[%s] %s %.2f %s %s %.2f %s"
        self.title = title
        self.total = total
        self.count = count
        self.chunk_size = chunk_size
        self.status = run_status or ""
        self.fin_status = fin_status or " " * len(self.status)
        self.unit = unit
        self.seq = sep

    async def __get_info(self):
        # [名称] 状态 进度 单位 分割线 总数 单位
        _info = self.info % (self.title, self.status,
                             self.count/self.chunk_size, self.unit, self.seq, self.total/self.chunk_size, self.unit)
        return _info

    async def refresh(self, count=1, status=None):
        self.count += count
        # if status is not None:
        self.status = status or self.status
        end_str = "\r"
        if self.count >= self.total:
            end_str = '\n'
            self.status = status or self.fin_status
        info = await self.__get_info()
        print(info, end=end_str)

if __name__ == "__main__":
    list_url = []
    fail_url_list = []

    # 在此更改采集的页数
    page = list(range(1,11))
    page_name = f'{page[0]}-{page[-1]}'

    # 新建文件夹
    b = os.path.abspath('.') + '\\' + page_name +'\\'
    if not os.path.exists(b):
        os.makedirs(b)

    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'}

    # 开始计时
    start = time.time()

    asyncio.run(login())

    print(f'用时{int((time.time()-start) // 60)}分{int((time.time()-start) % 60)}秒')
    input('回车以结束程序...')