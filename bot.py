import config
import telebot
import sqlite3 as sqlite
import re
import pickle
from peewee import *
from playhouse.sqlite_ext import *
import requests
import json
import pymorphy2
from telebot import types

#------ temp datas
mechatid = 5844335

#------

sys_data_file = 'data.pickle'

with open(sys_data_file, 'rb') as f:
	sys_data = pickle.load(f)
	f.close()

db = SqliteExtDatabase(config.db_name, threadlocals=True)

morph = pymorphy2.MorphAnalyzer() # для склонения слов


class Entry(Model):
	question = TextField()
	answer = TextField()

	class Meta:
		database = db

class FTSEntry(FTSModel):
	entry_id = IntegerField()
	content = TextField()

	class Meta:
		database = db

token = sys_data['token']
#token = '' #для ввода нового токена расскоментировать, добавить токен, запустить
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
	if sender_id in admins:
		return True
	else:
		return False
	
def getKey(dict, value):
	for i in dict:
		if dict[i] == value:
			return i


@bot.message_handler(commands = ['start'])
def greeting(message):
	greeting = '''Привет! Я буду твоим персональным помощником, 
	буду служить тебе верой и правдой и буду отвечать на твои вопросы. 
	Я еще молодой бот и мои знания будут постоянно пополняться. Удачной работы!'''
	bot.send_message(message.chat.id, greeting)

#@bot.message_handler(commands = ['add_reply'])
def add_reply(message):
	try:
		if message.chat.id != mechatid:
			username = message.from_user.username
			bot.send_message(mechatid, '@'+username+' '+message.text)
	except TypeError:
		print(message.text)
	sender_id = message.from_user.id
	if (sender_id in admins):
		#message.text = message.text[11:]
		delimiter = message.text.rfind("?")+1
		question = message.text[:delimiter]
		answer = message.text[delimiter:]
		answer = answer.lstrip()
		try:
			entry = Entry.create(
			      question=question,
			      answer=answer)
			FTSEntry.create(
			  entry_id=entry.id,
			  content='\n'.join((entry.question.lower(), entry.answer.lower())))
			response = "Вопрос успешно добавлен."
		except:
			response = "Что-то пошло не так, вопрос не добавлен."
		bot.send_message(message.chat.id, response)
	else:
		bot.send_message(message.chat.id, "Вы не можете добавлять вопросы")
	action = 'default'


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


@bot.message_handler(commands = ['show_questions'])
def show_questions(message):
	query = (FTSEntry
		         .select(Entry.question, Entry.answer)
		         .join(
		             Entry,
		             on=(FTSEntry.entry_id == Entry.id).alias('entry'))
		         .order_by(Entry.id)
		         .dicts())
	response = set()
	for row_dict in query:
			item = row_dict['question']+'\n'+row_dict['answer']+'\n\n'
			response.add(item)
	msg_text = ''
	if(len(response) == 0):
		msg_text = 'База вопросов пуста.'
	else:
		for item in response:
			msg_text += item
	bot.send_message(message.chat.id, msg_text)


#_________________ новый функционал
@bot.message_handler(commands = ['edit'])
def edit(message):
	if not checkUser(message):
		bot.send_message(message.chat.id, "У вас нет прав на редактирование")
		return False
	keyboard = types.InlineKeyboardMarkup()
	callback_button = types.InlineKeyboardButton(text="Добавить вопрос", callback_data="add_reply")
	keyboard.add(callback_button)
	callback_button = types.InlineKeyboardButton(text="Редактировать вопрос", callback_data="edit_reply")
	keyboard.add(callback_button)
	callback_button = types.InlineKeyboardButton(text="Удалить вопрос", callback_data="remove_reply")
	keyboard.add(callback_button)
	bot.send_message(message.chat.id, "Выберите действие", reply_markup=keyboard)

action = 'default'

@bot.callback_query_handler(func=lambda call: True)
def callback_edit(call):
	if call.data == 'add_reply':
		bot.send_message(chat_id=call.message.chat.id, text='Введите вопрос и ответ на него. Вопрос обязательно должен заканчиваться вопросительным знаком ("?")')
		action = 'add_reply'
	if call.data == 'edit_reply':
		bot.send_message(chat_id=call.message.chat.id, text='Введите вопрос, который Вы хотите отредактировать.')
		action = 'edit_reply'
	if call.data == 'remove_reply':
		bot.send_message(chat_id=call.message.chat.id, text='Введите вопрос, который Вы хотите удалить')
		action = 'remove_reply'




def search_answer(text):
	words = divide_into_words(text)
	response = set()
	for word in words:
		query = (FTSEntry
		         .select(Entry.question, Entry.answer)
		         .join(
		             Entry,
		             on=(FTSEntry.entry_id == Entry.id).alias('entry'))
		         .where(FTSEntry.match(word))
		         .dicts())
		for row_dict in query:
			item = row_dict['question']+'\n'+row_dict['answer']+'\n\n'
			response.add(item)
	if(len(response) == 0):
		response = 'Ничего не найдено.'
	result = ''
	for item in response:
		result += item
	return result

		
def divide_into_words(text): # функция не только делит строку на отдельные лексемы, 
							 #но и убирает из полученного множества вопросительные слова
	text = re.sub(r"(\W\s)|(\s\W\s)|(\W$)", r" ", text)
	text = text.lower()
	words = set(text.split())
	words.difference_update(config.interrogatives)
	prepositions = set()
	for word in words:
		if len(word) < 3:
			prepositions.add(word)
	words.difference_update(prepositions)
	cases = set()
	for word in words:
		w = morph.parse(word)[0]
		parse = w.lexeme
		for n in parse:
			cases.add(n.word)
	return cases


@bot.message_handler(content_types=['text'])
def main(message):
	try:
		if message.chat.id != mechatid:
			username = message.from_user.username
			bot.send_message(mechatid, '@'+username+' '+message.text)
	except TypeError:
		print(message.text)
	if action == 'add_reply':
		add_reply(message)
		return True
	if action == 'edit_reply':
		#add_reply(message)
		return True
	if action == 'remove_reply':
		#add_reply(message)
		return True
	checkUser(message)
	rewrite_sys_data()
	bot.send_message(message.chat.id, search_answer(message.text))

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





