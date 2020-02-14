#!/usr/bin/env python3
#-*-coding:utf-8-*-

import os

# 要删除重复内容的文件夹路径
filepath1 = ''
# 要保留的文件夹路径
filepath2 = ''

# 生成子文件列表
list1 = os.listdir(filepath1)
list2 = os.listdir(filepath2)

# 计数器
work = 0

for i in list1:
    if i in list2:
        work += 1
        # 删除重复文件
        os.remove(filepath1 + '\\' + i)

if work:
    print(f'已删除{work}个文件')
else:
    print('没有重复文件')