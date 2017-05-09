import config
from playhouse.sqlite_ext import SqliteExtDatabase
from peewee import *
from playhouse.sqlite_ext import *

db = SqliteExtDatabase(config.db_name, threadlocals=True)


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


entry = Entry.create(
      question='How I rewrote everything with golang',
      answer='Blah blah blah, type system, channels, blurgh')
FTSEntry.create(
  entry_id=entry.id,
  content='\n'.join((entry.question, entry.answer)))

entry = Entry.create(
  question='Why ORMs are a terrible idea',
  answer='Blah blah blah, leaky abstraction, impedance mismatch')
FTSEntry.create(
  entry_id=entry.id,
  content='\n'.join((entry.question, entry.answer)))

'''
SELECT entry.question 
FROM ftsentry
JOIN entry ON ftsentry.entry_id = entry.id
WHERE ftsentry MATCH "idea";


'''