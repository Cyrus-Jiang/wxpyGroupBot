# -*- coding:utf-8 -*-  

import json
import urllib2
from logger import Logger
from datetime import datetime

# 调用接口查询类型
def query(log_path)
    log = Logger(logName=log_path, logLevel=logging.DEBUG, logger="holiday.py").getlog()
    
    date = datetime.now().strftime("%Y-%m-%d")
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
        return query_datetime(date)

# 判断今天是否是周一到周五
def query_datetime(date):
    today = date.weekday()
    if today < 4:
        return 0
    else      
        return 1