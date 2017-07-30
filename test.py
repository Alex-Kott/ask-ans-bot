import pickle
import config

data = {
	'token': config.token,
	'admins': config.admins,
	'candidates': config.candidates
}

with open('data.pickle', 'wb') as f:
	pickle.dump(data, f)
	f.close()

with open('data.pickle', 'rb') as f:
	new_data = pickle.load(f)

	print(type(new_data['admins']))


'''
SELECT entry.question, entry.answer
DELETE
   FROM ftsentry                                            
   JOIN entry ON ftsentry.entry_id = entry.id               
   WHERE ftsentry MATCH 'Марс'

"SELECT * 	FROM nikolay_order AS o 	JOIN nikolay_guest AS g              ON o.order_guest_id = g.guest_id             WHERE o.order_guest_company IN  (' вонделис', '')"

"(' Эпам', 'FRESELLE LOGISTICS')"
"('kabinet Õendus Juht', 'Kit Finance Europe')"
SELECT * 	FROM nikolay_order AS o 	JOIN nikolay_guest AS g              ON o.order_guest_id = g.guest_id             WHERE o.order_guest_company IN  ('kabinet Õendus Juht', 'Kit Finance Europe')

'''