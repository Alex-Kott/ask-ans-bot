import config
import telebot
import sqlite3 as sqlite
import re
import pickle
from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase

sys_data_file = 'data.pickle'

with open(sys_data_file, 'rb') as f:
	sys_data = pickle.load(f)
	f.close()

db = SqliteExtDatabase(config.db_name, threadlocals=True)



token = sys_data['token']
admins = set(sys_data['admins'])
candidates = set(sys_data['candidates'])
try:
	sys_data['users']
	users = sys_data['users']
except KeyError:
	users = {}

bot = telebot.TeleBot(token)


def rewrite_sys_data():
	data = {
		'token': token,
		'admins': admins,
		'candidates': candidates,
		'users': users
	}
	with open(sys_data_file, "wb") as f:
		pickle.dump(data, f)

	

def set_admin(id, username):
	try:
		candidates.remove(username)
		admins.add(id)
	except ValueError:
		print("Candidate is not exist")
	rewrite_sys_data()
	


def checkUser(message):
	sender_id = message.from_user.id
	username = message.from_user.username
	if username in candidates:
		set_admin(sender_id, username)
	users[username] = int(sender_id)
	
def getKey(dict, value):
	for i in dict:
		if dict[i] == value:
			return i


@bot.message_handler(commands = ['add_reply'])
def add_reply(message):
	sender_id = message.from_user.id
	if (sender_id in admins):
		message.text = message.text[11:]
		delimiter = message.text.rfind("?")+1
		question = message.text[:delimiter]
		answer = message.text[delimiter:]
		answer = answer.lstrip()
		conn = sqlite.connect(config.db_name)
		cur = conn.cursor()
		query = '''
		INSERT INTO questions(`question`, `answer`)
		VALUES ('{0}', '{1}')
		'''.format(question, answer)
		try:
			cur.execute(query)
		except sqlite.DatabaseError as err:
			response = "Ошибка: "+err
		else:
			response = "Вопрос добавлен"
		conn.commit()
		cur.close()
		conn.close()
		bot.send_message(message.chat.id, response)
	else:
		bot.send_message(message.chat.id, "Вы не можете добавлять вопросы")


@bot.message_handler(commands = ['show_admins'])
def show_admins(message):
	resp = ''
	for i in admins:
		a = getKey(users, i)
		if a != None:
			resp += "@"+a+" "
	bot.send_message(message.chat.id, resp)

@bot.message_handler(commands = ['show_questions'])
def show_questions(message):
	resp = ''
	conn = sqlite.connect(config.db_name)
	curr = conn.cursor()
	query = 'SELECT * FROM questions'
	query_result = curr.execute(query)
	data = query_result.fetchall()
	response = ''
	if len(data) == 0:
		response = "База вопросов пуста"
		bot.send_message(message.chat.id, response)
	else:
		for i in data:
			response += "Вопрос: "+i[1]+"\nОтвет: "+i[2]+" \n\n"
		bot.send_message(message.chat.id, response)



@bot.message_handler(commands = ['add_admin'])
def add_admin(message):
	sender_id = message.from_user.id
	if (sender_id in admins):
		units = re.findall(r'@{1}\w*', message.text)
		for u in units:
			u = u[1:]
			candidates.add(u)
		rewrite_sys_data()


@bot.message_handler(commands = ['remove_admin'])
def remove_admin(message):
	sender_id = message.from_user.id
	if (sender_id in admins):
		units = re.findall(r'@{1}\w*', message.text)
		for u in units:
			u = u[1:]
			try:
				admins.remove(int(users[u]))
			except KeyError:
				bot.send_message(message.chat.id, "Админа {} не найдено".format(u))
		rewrite_sys_data()
		

@bot.message_handler(content_types=['text'])
def main(message):
	checkUser(message)
	bot.send_message(message.chat.id, message.text)
	rewrite_sys_data()

def init_db():
	conn = sqlite.connect(config.db_name)
	curr = conn.cursor()
	create_table = '''
	CREATE TABLE IF NOT EXISTS questions(
		`qid` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
		`question` TEXT NOT NULL,
		`answer` TEXT NOT NULL
	)'''
	curr.execute(create_table)
	conn.commit()
	conn.close()



if __name__ == '__main__':
	init_db()
	bot.polling(none_stop=True)





