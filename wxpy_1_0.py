# -*- coding: UTF-8 -*-  

# 导入模块
import os
import logging
import re
import holiday
from wxpy import *
from logger import Logger
from datetime import datetime
# 导入定时任务框架
from apscheduler.schedulers.background  import BackgroundScheduler

logging.basicConfig()

# loop标志
l_ci = 'ci'
l_clear = 'clear'
l_search = 'search'
# 需处理群聊list
groups = []
# 需处理群聊成员list
groups_players = []
# 特例群聊
special_group = None
# 打卡人数（与上面的list下表一一对应）
ci_nums = []
# 当前是否活动状态
is_activity = 1
# 图灵key
api_key = '***'
# 是否预先检查
is_check = 1
# 今日节假日类型（工作日为 False,节假日为 True）
today_holiday = False
# 节假日名称
holiday_name = None
# 已打卡提醒字符串
str_a = '已有{}人打卡'
# 未打卡提示字符串
str_b = '{} {},记得打卡哦'
# 早晨问候
str_m = '{},(^_^)v早上好'
# 统计结果通知字符串
str_r = '{} {},请注意检查是否已经打卡'
# 非目标用户字符串
str_n = '@{} 你好像不是目标用户哦'
# 欢迎新人入群
str_w = 'hey，欢迎你加入群聊！'
# log文件相对路径
log_path = r'log/'+ datetime.now().strftime("%Y-%m-%d") + '_WGB.txt'

try:
	os.mknod(log_path)
except OSError:
	# 如果文件已存在会抛OSError
	print("=====>OSrror")
finally:
	# 获取log实例对象
	log = Logger(logName=log_path, logLevel=logging.DEBUG, logger="wxpy_1_0.py").getlog()
	log.info("log has been successfully created")

# 初始化机器人，扫码登陆
bot = Bot(console_qr=True, cache_path=True)
# 启用puid属性(可作为用户唯一标识)
bot.enable_puid()
# 定位公司打卡群
def load_group():
	groups.append(ensure_one(bot.groups().search('版本测试群'.decode("utf-8"))))
	special_group = ensure_one(bot.groups().search('打卡了'.decode("utf-8")))
	groups.append(special_group)
	groups.append(ensure_one(bot.groups().search('总行三部群'.decode("utf-8"))))
	groups.append(ensure_one(bot.groups().search('基础平台'.decode("utf-8"))))
	groups.append(ensure_one(bot.groups().search('打卡异常'.decode("utf-8"))))

mia = 'mia|Mia|米娅|米亚|咪呀|蜜芽|miya|米雅'
pattern = re.compile(mia)

# 接入图灵机器人
tuling = Tuling(api_key)

# 目标用户对象
class player():
	def __init__(self,puid,member,have_clocked_in):
		self.puid = puid
		self.member = member
		self.have_clocked_in = have_clocked_in

# 加载目标用户集
def load_group_player(group_list):
	global ci_nums
	ci_nums = []
	for group in group_list:
		log.info('start load group:' + str(group.name))
		players = []
		for member in group:
			if 'xxx'.decode("utf-8") not in member.name and member != bot.self:
				players.append(player(member.puid, member, 0))
				log.info('add '+member.name)
			else:
				log.info('skip '+member.name)
		# 打印list里的所有成员
		log.info(players)
		ci_nums.append(0)
		groups_players.append(players)
	log.info('end load_group_player')

# load_group_player(groups)

# 循环遍历list查找指定用户或清空标志
def loop(type, puid, groups_index):
	log.info("start %s puid: %s group_index:%s" %(type, puid, groups_index))
	players = groups_players[groups_index]
	if type == l_search:
		for i in range(len(players)):
			if (puid == players[i].puid):
				return i
	else:
		no_ci = ''
		for player in players:
			if type == l_ci:
				if player.have_clocked_in == 0:
					no_ci += (' @' + player.member.name)
			if type == l_clear:
				player.have_clocked_in = 0
		# 清空该群组打卡次数
		if type == l_clear:
			ci_nums[groups_index] = 0
		return no_ci
	log.error("error loop")

# 欢迎新人入群
@bot.register(msg_types=NOTE)
def wlcm_new_player(msg):
	log.info(msg)
	if isinstance(msg.chat, Group) and msg.type == 'Note' and ('加入' in msg.text or '邀请' in msg.text):
		log.info(str_w)
		# 打卡群聊
		if msg.chat in groups:
			msg.chat.send(str_w + '用户列表将于明天更新生效')
		else:	
			msg.chat.send(str_w)

# 自动接受好友请求
@bot.register(msg_types=FRIENDS)
def auto_accept_friend(msg):
	new_friend = bot.accept_friend(msg.card)

# 使用图灵回复文字消息
@bot.register(msg_types=TEXT)
def tuling_auto_reply(msg):
	log.info(msg)
	# 如果是群聊但未被@则不做回复
	if isinstance(msg.chat, Group) and not msg.is_at and re.search(mia, msg.text) is None:
		log.info ("<TL> group no at")
		return
	else:
		log.info ("<TL> tuling auto reply")
		msg.text = pattern.sub('', msg.text)
		tuling.do_reply(msg)

# 打卡统计处理逻辑
def reply_group(msg, groups_index):
	log.info('start reply_group:' + str(groups_index))
	company_group = groups[groups_index]
	# 筛选命中信息处理
	if '微'.decode("utf-8") in msg.text and '交'.decode("utf-8") in msg.text and filter(str.isdigit, str(msg.text)) != '' and ('.' in msg.text or ':' in msg.text) or (company_group != special_group and msg.text.replace(' ','').isdigit()):
		index = loop(l_search, msg.member.puid, groups_index)
		log.info("index:" + str(index))
		if index is None:
			company_group.send(str_n.format(msg.member.name).decode("utf-8"))
		else:
			# 获取该群聊的成员列表
			players = groups_players[groups_index]
			# 如果未曾打卡且在活动状态,则计入已打卡名单
			if players[index].have_clocked_in == 0 and is_activity == 1:
				log.info('reply_group: true')
				players[index].have_clocked_in = 1
				ci_nums[groups_index] += 1
				ci_num = ci_nums[groups_index]
				log.info(str_a.format(ci_num).decode("utf-8"))
				if ci_num == len(players):
					company_group.send('Nice,打卡完毕'.decode("utf-8"))
				elif ci_num%5==0:
					company_group.send(str_a.format(ci_num).decode("utf-8"))
				elif len(players) - ci_num == 3:
					hard = ''
					if datetime.now().hour > 20:
						hard = '辛苦了'.decode("utf-8")
					no_ci = loop(l_ci, '', groups_index)
					company_group.send(str_b.format(no_ci,hard).decode("utf-8"))
				elif ci_num < 4:
					if datetime.now().hour < 9:
						company_group.send(str_m.format(msg.member.name).decode("utf-8"))
	else:
		log.info('reply_group: false')
	tuling_auto_reply(msg)

# 遍历群聊列表群发信息
def loop_send(group_list, text):
	for group in group_list:
		group.send(text)

# 进行节日问候
def send_bless():
	log.info('start send_bless')
	if holiday_name != None and holiday_name != '':
		# --temp--
		today = datetime.now().date()
		if(today.day != 5):
			log.info('today skip+%d' %today.day)
			return
		# --temp--
		log.info('holiday_name:' + holiday_name)
		loop_send(bot.groups(), '@All people , Happy '+ holiday_name)

# 每日重新加载一次打卡目标集
def reload_daily():
	log.info('start reload_daily')
	global groups,groups_players
	groups = []
	groups_players = []
	load_group()
	load_group_player(groups)
	
# 每日凌晨查询是否节假日
def query_holiday():
	log.info('start query_holiday')
	global today_holiday, holiday_name
	today_holiday, holiday_name = holiday.query_h()
	if today_holiday:
		global is_activity
		is_activity = 0
		send_bless()
	log.info('end query_holiday:' + str(today_holiday) + str(holiday_name))

# 程序首次运行进行加载用户列表，并查询节假日
reload_daily()
query_holiday()

# 处理指定群聊信息的文字信息
@bot.register(groups, TEXT)
def reply_group_0(msg):
	reply_group(msg, groups.index(msg.chat))

# 仅预先检查输出待打卡统计信息,不停止接受打卡请求
def check_job():
	if today_holiday:
		log.info('skip check_job')
		return
	log.info('start check_job')
	global is_check
	is_check = 1
	multiple_loops(l_ci)
	log.info('end check_job')

# 结算统计信息并输出,结束本轮记录
def result_job():
	global is_activity,is_check
	is_activity = 0
	is_check = 0
	# 节假日则跳过
	if today_holiday:
		log.info('skip result_job')
		return
	log.info('start result_job')
	multiple_loops(l_ci)
	log.info('end result_job')

# 清空打卡标志,启动下一轮记录
def redo_job():
	# 节假日则跳过
	if today_holiday:
		log.info('skip redo_job')
		return
	log.info('start redo_job')
	multiple_loops(l_clear)
	global is_activity
	is_activity = 1
	log.info('end redo_job')

# 对所有群聊进行循环处理指定操作
def multiple_loops(type):
	for i in range(len(groups_players)):
		no_ci = loop(type, '', i)
		# 如果存在未打卡则发信息提醒
		if type == l_ci and ci_nums[i] != len(groups_players[i]):
			hard = ''
			if datetime.now().hour > 20:
				hard = '辛苦了'.decode("utf-8")
			if is_check == 0:
				groups[i].send(str_r.format(no_ci, hard))
			else:
				groups[i].send(str_b.format(no_ci, hard))

# 定时发信存活确认
def survival_confirm():
	log.info('==== survival confirmation ====')
	groups[0].send('Im Okay!')

# BackgroundScheduler 定时监控
scheduler = BackgroundScheduler()
scheduler.add_job(check_job, 'cron', hour=8, minute=53, timezone='PRC')
scheduler.add_job(result_job, 'cron', hour=8, minute=59, timezone='PRC')
scheduler.start()
scheduler.add_job(redo_job, 'cron', hour=16, minute=40, timezone='PRC')
scheduler.add_job(check_job, 'cron', hour=21, minute=10, timezone='PRC')
scheduler.add_job(result_job, 'cron', hour=21, minute=40, timezone='PRC')
scheduler.add_job(redo_job, 'cron', hour=5, minute=40, timezone='PRC')
scheduler.add_job(query_holiday, 'cron', hour=0, minute=20, timezone='PRC')
scheduler.add_job(reload_daily, 'cron', hour=5, minute=10, timezone='PRC')
scheduler.add_job(survival_confirm, 'interval', minutes=20, timezone='PRC')

# 堵塞
embed()
