# -*- coding: UTF-8 -*-

# 导入模块
from wxpy import *
# 导入定时任务框架
from apscheduler.schedulers.background  import BackgroundScheduler
from datetime import datetime
import logging
import os
from logger import Logger

logging.basicConfig()

# 群聊成员list
players = []
# 打卡人数
ci_num = 0
# 当前是否活动状态
is_activity = 1
# 已打卡提醒字符串
str_a = '已有{}人打卡'
# 未打卡提示字符串
str_b = '{},请不要忘记打卡'
# 统计结果通知字符串
str_r = '{},请检查是否已打卡'
# 非目标用户字符串
str_n = '@{} 你好像不是目标用户哦'
# log文件相对路径
log_path = r'log/'+ datetime.now().strftime("%Y-%m-%d") + '_WGB.txt'

try：
    # 如果文件已存在会抛OSError
    os.mknod(log_path)
finally:
    # 获取log实例对象
    log = Logger(logname=log_path, loglevel=logging.DEBUG, logger="wxpy_1_0.py").getlog()
    log.info("log has been successfully created")


# 初始化机器人，扫码登陆
bot = Bot(console_qr=True, cache_path=True)
# 启用puid属性(可作为用户唯一标识)
bot.enable_puid()
# 定位公司打卡群
company_group = ensure_one(bot.groups().search('打卡了'.decode("utf-8")))
# 接入图灵机器人
tuling = Tuling(api_key='***')

# 目标用户对象
class player():
    def __init__(self,puid,member,have_clocked_in):
        self.puid = puid
        self.member = member
        self.have_clocked_in = have_clocked_in

# 加载目标用户集
for member in company_group:
    log.info(member)
    if 'xxx'.decode("utf-8") not in member.name and 'App' not in member.name:
        players.append(player(member.puid, member, 0))

# 打印list里的所有成员
log.info(type(players),players)

# 循环遍历list查找指定用户
def loop(type, puid):
    log.info("start " + type + puid)
    if type == 'search':
        for i in range(len(players)):
            if (puid == players[i].puid):
                return i
    else:
        no_ci = ''
        for player in players:
            if type == 'ci':
                if player.have_clocked_in == 0:
                    no_ci += (' @' + player.member.name)
            if type == 'clear':
                player.have_clocked_in = 0
        return no_ci
    log.info("error loop:" + type + puid)

# 使用图灵回复文字消息
@bot.register(msg_types=TEXT)
def tuling_auto_reply(msg):
    log.info(msg)
    # 如果是群聊但未被被@则不做回复
    if isinstance(msg.chat, Group) and not msg.is_at:
        log.info ("<TL> group no at")
        return
    else:
        log.info ("<TL> tuling auto reply")
        tuling.do_reply(msg)

# 处理指定群聊信息的文字信息
@bot.register(company_group, TEXT)
def reply_group(msg):
    # 筛选命中信息处理
    if '微'.decode("utf-8") in msg.text and '交'.decode("utf-8") in msg.text and filter(str.isdigit, msg.text) != '' and '.' in msg.text:
        index = loop('search', msg.member.puid)
        log.info("index:",index)
        if index is None:
            company_group.send(str_n.format(msg.member.name).decode("utf-8"))
        else:
            # 如果未曾打卡且在活动状态,则计入已打卡名单
            if players[index].have_clocked_in == 0 and is_activity == 1:
                log.info('reply_group:true')
                players[index].have_clocked_in = 1
                global ci_num
                ci_num += 1
                log.info(str_a.format(ci_num).decode("utf-8"))
                if ci_num == len(players):
                    company_group.send('Nice,打卡完毕'.decode("utf-8"))
                elif ci_num%5==0:
                    company_group.send(str_a.format(ci_num).decode("utf-8"))
                elif len(players) - ci_num == 3:
                    no_ci = loop('ci', '')
                    company_group.send(str_b.format(no_ci).decode("utf-8"))
    else:
        log.info('reply_group: false')
    tuling_auto_reply(msg)

# 输出统计信息,结束本轮记录
def result_job():
    log.info('start result_job')
    if ci_num != len(players) :
        no_ci = loop('ci', '')
        company_group.send(str_r.format(no_ci))
    global is_activity
    is_activity = 0
    log.info('end result_job')

# 清空标志,启动下一轮记录
def redo_job():
    log.info('start redo_job')
    loop('clear', '')
    global is_activity, ci_num
    is_activity = 1
    ci_num = 0
    log.info('end redo_job')

# BackgroundScheduler 定时监控
scheduler = BackgroundScheduler()
scheduler.add_job(result_job, 'cron', day_of_week='0-4', hour=8, minute=59, timezone='PRC')
scheduler.start()
scheduler.add_job(redo_job, 'cron', day_of_week='0-4', hour=16, minute=40, timezone='PRC')
scheduler.add_job(result_job, 'cron', day_of_week='0-4', hour=21, minute=30, timezone='PRC')
scheduler.add_job(redo_job, 'cron', day_of_week='0-4', hour=5, minute=0, timezone='PRC')

embed()
