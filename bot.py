import telebot
import sqlite3
import re
import pickle
'''
from config import token as token
from config import admins as admins
from config import candidates as candidates'''

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
		bot.send_message(message.chat.id, message.text)
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



if __name__ == '__main__':
	print(admins)
	print(candidates)
	print(users)
	#users.clear()
	#admins.clear()
	#admins.add(5844335)'''
	bot.polling(none_stop=True)






def lol():
	con = sqlite3.connect('bot.db')
	cur = con.cursor()
	create_questions = '''
	CREATE TABLE questions(
		qid INTEGER NOT NUL AUTOINCREMENT,
		qtext TEXT NOT NULL,
		answer TEXT NOT NULL
	)'''
	cur.execute(create_questions)
	con.commit()

	con.close()