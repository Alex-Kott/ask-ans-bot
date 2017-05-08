import telebot
import sqlite3
import re
import pickle
from peewee import *
from playhouse.sqlite_ext import *

config_file = 'data.pickle'

with open(config_file, 'rb') as f:
	config = pickle.load(f)
	f.close()



token = config['token']
admins = set(config['admins'])
candidates = set(config['candidates'])
try:
	config['users']
	users = config['users']
except KeyError:
	users = {}

bot = telebot.TeleBot(token)


def rewriteConfig():
	data = {
		'token': token,
		'admins': admins,
		'candidates': candidates,
		'users': users
	}
	with open(config_file, "wb") as f:
		pickle.dump(data, f)

	

def set_admin(id, username):
	try:
		candidates.remove(username)
		admins.add(id)
	except ValueError:
		print("Candidate is not exist")
	rewriteConfig()
	


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
		question = re.findall(r'[\w|\s]*\?', message.text)
		answer = re.findall(r'[\?](\w|\W)*\$', message.text)
		answer = answer[1:]
		print(question)
		print(answer)
		"""
		conn = sqlite3.connect('ask-ans-bot.db')
		curr = conn.cursor()
		insert_query = '''
		INSERT INTO questions(`qtext`, `answer`)
		VALUES ('{0}', '{1}')
		'''.format(question, answer)
		print(insert_query)
		curr.execute(insert_query)
		conn.commit()
		bot.send_message(message.chat.id, message.text)"""
	else:
		bot.send_message(message.chat.id, "Lol you")


@bot.message_handler(commands = ['show_admins'])
def show_admins(message):
	resp = ''
	for i in admins:
		a = getKey(users, i)
		if a != None:
			resp += "@"+a+" "
	bot.send_message(message.chat.id, resp)



@bot.message_handler(commands = ['add_admin'])
def add_admin(message):
	sender_id = message.from_user.id
	if (sender_id in admins):
		units = re.findall(r'@{1}\w*', message.text)
		for u in units:
			u = u[1:]
			candidates.add(u)
		rewriteConfig()


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
		rewriteConfig()
		

@bot.message_handler(content_types=['text'])
def main(message):
	checkUser(message)
	bot.send_message(message.chat.id, message.text)
	rewriteConfig()

def init_db():
	conn = sqlite3.connect('ask-ans-bot.db')
	curr = conn.cursor()
	create_table = '''
	CREATE TABLE IF NOT EXISTS questions(
		`qid` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
		`qtext` TEXT NOT NULL,
		`answer` TEXT NOT NULL
	)'''
	curr.execute(create_table)
	conn.commit()
	conn.close()



if __name__ == '__main__':
	init_db()
	bot.polling(none_stop=True)





