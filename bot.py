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
import bot_strings as bs # это строки, определённые в bot_strings.py

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

def add_reply(message):
	try:
		if message.chat.id != mechatid:
			username = message.from_user.username
			bot.send_message(mechatid, '@'+username+' '+message.text)
	except TypeError:
		print(message.text)
	sender_id = message.from_user.id
	if (sender_id in admins):
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
			response = bs.smth_went_wrong
		bot.send_message(message.chat.id, response)
	else:
		bot.send_message(message.chat.id, "Вы не можете добавлять вопросы")

def remove_reply(message):  # функция remove_reply запускает процедуру удаления вопросов, а delete_reply непосредственно её выполняет
	sender_id = message.from_user.id
	if not checkUser(message):
		bot.send_message(message.chat.id, bs.you_have_no_power)
		return False
	words = divide_into_words(message.text)
	response = {}
	for word in words:
		query = (FTSEntry
		         .select(Entry.id, Entry.question, Entry.answer)
		         .join(
		             Entry,
		             on=(FTSEntry.entry_id == Entry.id).alias('entry'))
		         .where(FTSEntry.match(word))
		         .dicts())
		for row_dict in query:
			response[row_dict['id']] = row_dict['question']
	if(len(response) == 0):
		msg = bs.nthng_found
		bot.send_message(message.chat.id, msg)
		return False
	keyboard = types.InlineKeyboardMarkup()
	for i in response:
		callback_button = types.InlineKeyboardButton(text=response[i], callback_data="remove_{}".format(i))
		keyboard.add(callback_button)
	bot.send_message(message.chat.id, bs.select_reply_for_removing, reply_markup=keyboard)

def delete_reply(chat_id, reply_id): # функция remove_reply запускает процедуру удаления вопросов, а delete_reply непосредственно её выполняет
	query = (FTSEntry
	         .delete()
	         .where(FTSEntry.entry_id == reply_id))
	res1 = query.execute()
	query = (Entry
	         .delete()
	         .where(Entry.id == reply_id))
	res2 = query.execute()
	if res1 and res2:
		bot.send_message(chat_id, bs.reply_removed)
	else:
		bot.send_message(chat_id, bs.smth_went_wrong)


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
		response = bs.nthng_found
	result = ''
	for item in response:
		result += item
	return result

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
	if not checkUser(message):
		bot.send_message(message.chat.id, bs.you_have_no_power)
		return False
	sender_id = message.from_user.id
	if (sender_id in admins):
		units = re.findall(r'@{1}\w*', message.text)
		for u in units:
			u = u[1:]
			candidates.add(u)
		bot.send_message(message.chat.id, bs.admin_added)
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


#_________________ 
@bot.message_handler(commands = ['edit'])
def edit(message):
	if not checkUser(message):
		bot.send_message(message.chat.id, bs.you_have_no_power)
		return False
	keyboard = types.InlineKeyboardMarkup()
	callback_button = types.InlineKeyboardButton(text=bs.add_reply, callback_data="add_reply")
	keyboard.add(callback_button)
	callback_button = types.InlineKeyboardButton(text=bs.add_admin, callback_data="add_admin")
	keyboard.add(callback_button)
	#callback_button = types.InlineKeyboardButton(text=bs.edit_reply, callback_data="edit_reply")
	#keyboard.add(callback_button)
	callback_button = types.InlineKeyboardButton(text=bs.remove_reply, callback_data="remove_reply")
	keyboard.add(callback_button)
	callback_button = types.InlineKeyboardButton(text=bs.remove_admin, callback_data="remove_reply")
	keyboard.add(callback_button)
	bot.send_message(message.chat.id, "Выберите действие", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def callback_edit(call):
	if call.data == 'add_reply':
		markup = types.ForceReply(selective=False)
		bot.send_message(chat_id=call.message.chat.id, text=bs.enter_new_reply, reply_markup=markup)
	if call.data == 'edit_reply':
		markup = types.ForceReply(selective=False)
		bot.send_message(chat_id=call.message.chat.id, text=bs.edit_reply, reply_markup=markup)
	if call.data == 'remove_reply':
		markup = types.ForceReply(selective=False)
		bot.send_message(chat_id=call.message.chat.id, text=bs.enter_remove_reply, reply_markup=markup)
	if re.match(r'remove_[0-9]', call.data):
		reply_id = re.findall(r'\d+$', call.data)
		delete_reply(call.message.chat.id, reply_id[0])
	if call.data == 'add_admin':
		markup = types.ForceReply(selective=False)
		bot.send_message(chat_id=call.message.chat.id, text=bs.enter_new_admin, reply_markup=markup)
	if call.data == 'remove_admin':
		markup = types.ForceReply(selective=False)
		bot.send_message(chat_id=call.message.chat.id, text=bs.enter_remove_admin, reply_markup=markup)

@bot.message_handler(content_types=['text'])
def main(message):
	try:
		if message.chat.id != mechatid:
			username = message.from_user.username
			bot.send_message(mechatid, '@'+username+' '+message.text)
	except TypeError:
		print(message.text)
	if message.reply_to_message != None:
		if message.reply_to_message.text == bs.enter_new_reply:
			add_reply(message)
			return True
		if message.reply_to_message.text == bs.edit_reply:
			edit_reply(message)
			return True
		if message.reply_to_message.text == bs.enter_remove_reply:
			remove_reply(message)
			return True
		if message.reply_to_message.text == bs.enter_new_admin:
			add_admin(message)
			return True
		if message.reply_to_message.text == bs.enter_remove_admin:
			remove_admin(message)
			return True
	checkUser(message)
	rewrite_sys_data()
	bot.send_message(message.chat.id, search_answer(message.text))




		
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





