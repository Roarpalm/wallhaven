#### 自学Python一个月写出来的第一个爬虫，往代码里填入自己的账号密码就可以使用


## 2020年2月3日更新(1.1)：
- 改用愚蠢的手动拆分成4段代码给4个线程，意外的比以前更高效，不知道有没有简便的写法

- 有些图片分辨率过大导致超时，可以复制失败url到 download_again.py 再下一遍，或者手动点击链接进网站右键保存

## 2020年2月3日更新(1.2):
- 代码更简洁了

## 2020年2月3日更新(1.3):

- 会新建文件夹了

## 2020年2月4日更新(1.4):
- 在多页批量下载的时候，下载到中途会出现各种报错，大概一半的图片会受影响而下载失败（10060，10054等我看不懂的错误）

- 暂不清楚是我的网络问题还是网站有反爬虫

- 建议一次下载100张图以内

- download_again 新加多线程下载

## 2020年2月9日更新(1.5):
- 优化了代码，并显示线程名

## 2020年2月12日更新(1.6):
- 代码更简洁了，用线程池代替线程模块