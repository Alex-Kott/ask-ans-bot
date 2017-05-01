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