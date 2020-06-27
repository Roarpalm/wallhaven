## 历史的垃圾桶：
历史版本，仅作备份

## exe程序：
打包好了一个exe给不懂代码的小朋友使用

## exe-setu-machine.py:
exe版的代码

## New_Super_setu-machine.py:
真正的代码，往里面填入账号密码就可以使用

## new GUI Wallhaven Setu-machine.py
使用 Pyside2 做ui的代码，往里面填入账号密码就可以使用

Pyside2 的包较大，可以用豆瓣的源进行安装

```pip install pyside2 -i https://pypi.douban.com/simple/```

## wallhaven.ui
```new GUI Wallhaven Setu-machine.py``` 的ui文件

## Wallhaven Setu Machine.py
The Engish version with command line.

## 说明
![Instructions](imgs/Instructions.jpg?raw=true)
- - - -
### 版本信息

#### 2020年2月3日更新(1.1)：
改用愚蠢的手动拆分成4段代码给4个线程，意外的比以前更高效，不知道有没有简便的写法

有些图片分辨率过大导致超时，可以复制失败url到 ```download_again.py``` 再下一遍，或者手动点击链接进网站右键保存

#### 2020年2月3日更新(1.2):
代码更简洁了

#### 2020年2月3日更新(1.3):

会新建文件夹了

#### 2020年2月4日更新(1.4):
在多页批量下载的时候，下载到中途会出现各种报错，大概一半的图片会受影响而下载失败（10060，10054等我看不懂的错误）

暂不清楚是我的网络问题还是网站有反爬虫

建议一次下载100张图以内

```download_again()``` 新加多线程下载

#### 2020年2月9日更新(1.5):
优化了代码，并显示线程名

#### 2020年2月12日更新(1.6):
代码更简洁了，用线程池代替线程模块

#### 2020年2月12日更新(1.7):
优化代码

#### 2020年2月14日更新(1.8):
爬完过去一年的toplist前30页之后我开始爬过去6个月的toplist，准备了一份url文本，用以剔除大量重复内容

新增 delete_same_file 用以删除文件夹里的重复图片

#### 2020年2月14日更新(1.9):
改用8线程

终于想起来用 ```try...except...``` 来捕获异常，能正确提取失败url了

#### 2020年2月17日更新(2.0):
与其自己手动复制失败的url，不如再写个循环让失败的url在主程序里继续跑，省事多了，但也更耗时了

不清楚下载失败的具体原因，猜测是网络问题，因为有的第一遍下不来第二遍第三遍就能下得动

为了解决大量重复图片的问题，现在程序会生成一个文本文件用以储存已经爬过的url，在代码中新增 ```delete_url() ```函数，在 ```get_img()``` 里面新增一行判断，用以避免重复下载

需要注意的是文本没有用'[]'括起来，所以还需用完手动添加，用前手动删除

#### 2020年2月17日更新(2.1):
删除 ```delete_url()``` 函数

删除重复代码

重写 ```write_url()``` 函数，现在无需手动改文本文件，能顺利读取和新增url

新增 ```write_fail_url()``` 函数，记录那些死活下不动的url

#### 2020年2月19日更新(3.0):
重大更新！

重写部分用到 ```beautifulsoup``` 的代码，更简洁

终于发现了之前频繁下载失败的原因：当我开多个线程去解析网页获取图片url的时候就会失败，线程开得越多失败率越高

不清楚是代码问题还是网站问题

总之我把解析网页这部分单独拎出来顺序执行，执行完再开8线程进行下载，这样失败就只剩下图片太大下不来这一种可能

#### 2020年2月19日更新(3.1):
掌握 ```beautifulsoup```，可以不用 ```etree ```了

#### 2020年2月20日更新(4.0):
重大更新之后的重大更新！

用异步IO库：```asyncio, aiohttp``` 重构几乎全部代码！

下载速度比旧版线程有了质的飞越

现存问题：解析网页无论是异步并行还是多线程，都会导致解析失败，可能是网站的限制

无奈我限制只能并行1个异步，这里成了最耗时的部分

#### 2020年2月21日更新(4.1):
修改下载代码，分段下载有点坑

取消下载限制

重写 ```download_again()```，配合 ```fail.txt``` 可以直接使用了

#### 2020年2月22日更新(5.0):
我是傻逼

之前的爬虫流程都是：爬排行榜得到各图的网页链接-进入各网页链接获取各图片链接-下载图片

我定睛一看，这图片链接怎么长得跟网页链接那么像呢

```python
page_url = 'https://wallhaven.cc/favorites/fav/73q5p3' # 网页链接
img_url = 'https://w.wallhaven.cc/full/73/wallhaven-73q5p3.jpg' # 图片链接

small_url = url.split('/')[-1]
little_url = small_url[0:2]
full_url = 'https://w.wallhaven.cc/full/' + little_url + '/wallhaven-' + small_url + '.jpg'
```
于是乎，更新5.0算了，从网页链接推导得到图片链接，直接开全速下载，省去一个个等待网页解析的时候，省去连接超时被服务器断开的烦恼

#### 2020年2月27日更新(6.0):
将 ```Super_setu_machine.py```, ```download_again.py``` 和 ```fail.txt``` 扫进历史的垃圾堆

全新 ```New_Super_setu_machine.py``` 登场

采用断点续传，不成功自动重新循环，彻底解决图片下载失败的问题， 真正做到一键爬图，享受立即开冲的爽快

#### 2020年2月27日更新(6.1):
引入 ```tqdm``` 模块，虽然没处理完善但下载时可以看到程序在动，避免产生程序卡死的想法

#### 2020年2月28日更新(6.2):
简写部分代码

采用 ```Python3.7``` 版本之后才有的 ```asyncio.run()``` 函数运行主程序

#### 2020年2月29日更新(6.2):
嗨呀，今年有29号

解决tqdm显示问题

#### 2020年3月3日更新(6.3):
修复不能正确剔除重复url的bug

```asyncio.run()``` 有问题，改回去

新增 ```setu-machine.exe``` 搭配 ```all-url.txt``` 无需安装Python环境即可运行

#### 2020年3月4日更新(6.4):
修复下载失败死循环的问题

#### 2020年3月13日更新(6.5):
并没有修复下载失败死循环的问题，只是不写死循环用有限循环了

把会陷入死循环的url写入文本

稍微修改 ```get_url()``` 的打印方式

#### 2020年3月23日更新(6.6):
稍微修改 ```img_download()``` 函数

找到了死活下载失败的原因：有些图片的header里没有 ```content-length```

但是我不知道怎么解决，直接跳过，建议手动打开

#### 2020年4月14日更新(6.7):
久违的更新

把代码用 ```class``` 封装起来，更加规范且优雅

exe版本进行了更新

#### 2020年4月17日更新(7.0):
加了个简单的GUI界面

把程序拆分为 爬取 和 下载 两部分，并且会实时对txt文本进行修改，这样即使下载一半意外中断，只需再次点击下载，无需多余操作

#### 2020年4月18日更新(7.1):
小修小补

#### 2020年5月4日更新(7.2):
用 Pyside2 写了一套新的UI，更好看，操作简单

#### 2020年5月5日更新(7.3):
修复了 ```new GUI Wallhaven Setu-machine.py``` 中 在子线程更新GUI导致程序崩溃的bug

#### 2020年6月27日更新(7.4):
特意给这位朋友写了个英文版，没有图形界面