#!/usr/bin/env python
# -*- coding:utf-8 -*-

import pymysql

#连接数据库
conn = pymysql.connect(host='127.0.0.1',port= 3306,user = 'root',passwd='',db='test')
#创建游标
cur = conn.cursor()

#向数据库test表中插入数据
ret = cur.executemany("insert into test values()")
#提交
conn.commit()
#关闭指针对象
cur.close()
#关闭连接对象
conn.close()
#打印结果
print(ret)