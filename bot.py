import config
import telebot
import sqlite3

bot = telebot.TeleBot(config.token)

def setAdmin(username):
	return True



@bot.message_handler(content_types=['text'])
def repeat(message):
	bot.send_message(message.chat.id, message.text)



if __name__ == '__main__':
	bot.polling(none_stop=True)

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