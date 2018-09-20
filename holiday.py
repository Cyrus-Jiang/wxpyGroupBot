# -*- coding:utf-8 -*-  

import json
import logging
import urllib2
from logger import Logger
from datetime import datetime
import chinese_calendar as calendar

# 使用chinese_calendar
def query_h():
    today = datetime.now()
    on_holiday, holiday_name = calendar.get_holiday_detail(today)
    return on_holiday, holiday_name

# 调用接口查询类型(这个接口必须申请授权码，现在使用chinese_calendar模块代替)
def query(log_path):
    log = Logger(logName=log_path, logLevel=logging.DEBUG, logger="holiday.py").getlog()
    
    date = datetime.now().strftime("%Y%m%d")
    server_url = "http://www.easybots.cn/api/holiday.php?d="
 
    api_url_request = urllib2.Request(server_url+date)
    api_response = urllib2.urlopen(api_url_request)
 
    api_data= json.loads(api_response.read())
 
    log.info(api_data)
 
    if api_data[date]=='0':
        log.info('This day is weekday')
        return 0
    elif api_data[date]=='1':
        log.info('This day is weekend')
        return 1
    elif api_data[date]=='2':
        log.info('This day is holiday')
        return 2
    else:
    	log.error('Parsing failure, use datetime')
        return query_weekday(date)

# 判断今天是否是周一到周五
def query_weekday(date):
    today = date.weekday()
    if today < 4:
        return 0
    else:
        return 1