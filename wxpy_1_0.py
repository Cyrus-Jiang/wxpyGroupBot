# -*- coding: UTF-8 -*-

# 导入模块
from wxpy import *
# 导入定时任务框架
from apscheduler.schedulers.background  import BackgroundScheduler
from datetime import datetime
import logging

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


# 初始化机器人，扫码登陆
bot = Bot(console_qr=True, cache_path=True)
# 启用puid属性(可作为用户唯一标识)
bot.enable_puid()
# 定位公司打卡群
company_group = ensure_one(bot.groups().search('打卡了'.decode("utf-8")))
# 接入图灵机器人
tuling = Tuling(api_key='***')

# 成员对象
class player():
    def __init__(self,puid,member,have_clocked_in):
        self.puid = puid
        self.member = member
        self.have_clocked_in = have_clocked_in

# 加载目标用户集
for member in company_group:
    print(member)
    if '杨柳'.decode("utf-8") not in member.name and 'App' not in member.name:
        players.append(player(member.puid, member, 0))

# 打印list里的所有成员
print(type(players),players)

# 循环遍历list查找指定用户
def loop(type, puid):
    print("start " + type + puid)
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
    print("error loop" + type + puid)

# 使用图灵回复文字消息
@bot.register(msg_types=TEXT)
def tuling_auto_reply(msg):
    print ("<TL> tuling auto reply")
    tuling.do_reply(msg)

# 处理指定群聊信息的文字信息
@bot.register(company_group, TEXT)
def reply_group(msg):
    print(msg)
    if '微'.decode("utf-8") in msg.text and '交'.decode("utf-8") in msg.text and ('0' in msg.text or '1' in msg.text or '2' in msg.text or '.' in msg.text):
        index = loop('search', msg.member.puid)
        print("====>",index)
        if index is None:
            company_group.send(str_n.format(msg.member.name).decode("utf-8"))
        else:
            # 如果未曾打卡且在活动状态,则计入已打卡名单
            if players[index].have_clocked_in == 0 and is_activity == 1:
                print('true')
                players[index].have_clocked_in = 1
                global ci_num
                ci_num += 1
                print(str_a.format(ci_num).decode("utf-8"))
                if ci_num == len(players):
                    company_group.send('Nice,打卡完毕'.decode("utf-8"))
                elif ci_num%5==0:
                    company_group.send(str_a.format(ci_num).decode("utf-8"))
                elif len(players) - ci_num == 3:
                    no_ci = loop('ci', '')
                    company_group.send(str_b.format(no_ci).decode("utf-8"))
    elif msg.is_at:
        # 如果被@则回复群聊信息
        tuling_auto_reply(msg)
    else:
        print('false')

# 输出统计信息,结束本轮记录
def result_job():
    print('start result_job')
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if ci_num != len(players) :
        no_ci = loop('ci', '')
        company_group.send(str_r.format(no_ci))
    global is_activity
    is_activity = 0
    print('end result_job')

# 清空标志,启动下一轮记录
def redo_job():
    print('start redo_job')
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    loop('clear', '')
    global is_activity, ci_num
    is_activity = 1
    print('ci_num:' + ci_num)
    ci_num = 0
    print('end redo_job')

# BackgroundScheduler 定时监控
scheduler = BackgroundScheduler()
scheduler.add_job(result_job, 'cron', day_of_week='0-4', hour=8, minute=59, timezone='PRC')
scheduler.start()
scheduler.add_job(redo_job, 'cron', day_of_week='0-4', hour=16, minute=40, timezone='PRC')
scheduler.add_job(result_job, 'cron', day_of_week='0-4', hour=21, minute=30, timezone='PRC')
scheduler.add_job(redo_job, 'cron', day_of_week='0-4', hour=5, minute=0, timezone='PRC')

embed()
