from pymongo import MongoClient
from faker import Faker
import hashlib, os, binascii
import random
from datetime import date

fake = Faker()

cluster = MongoClient('mongodb+srv://matcha:password13@matcha-g1enx.mongodb.net/test?retryWrites=true&w=majority')
db = cluster['Matcha']
col = db['Users']
noti = db['Notifications']
chatsdb = db['Chats']

# cluster = MongoClient('localhost', 27017)
# db = cluster.matcha
# col = db.users
# noti = db.Notifications

def hash_password(password):
	salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
	pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
	pwdhash = binascii.hexlify(pwdhash)
	return (salt + pwdhash).decode('ascii')

def createUsers():
	col.delete_many( { } )
	noti.delete_many( { } )
	chatsdb.delete_many( { } )
	i = 0
	while (i < 500):
		# sexual orientation
		randSO = random.randint(0, 2)
		if (randSO == 0):
			SO = 'heterosexual'
		elif (randSO == 1):
			SO = 'homosexual'
		elif (randSO == 2):
			SO = 'bisexual'
		# gender, name, surname
		randGen = random.randint(0, 1)
		if (randGen == 0): # male
			gender = 'male'
			name = fake.first_name_male()
			while (len(name) < 5):
				name = fake.first_name_male()
			surname = fake.last_name_male()
			while (len(surname) < 6):
				surname = fake.last_name_male()
		elif (randGen == 1): #female
			gender = 'female'
			name = fake.first_name_female()
			surname = fake.last_name_female()
			while (len(name) < 5):
				name = fake.first_name_female()
			surname = fake.last_name_female()
			while (len(surname) < 6):
				surname = fake.last_name_female()
		nameLen = len(name)
		surLen = len(surname)
		first_letter = name[0]
		second_letter = name[random.randint(1, nameLen - 1)]
		third_letter = name[random.randint(1, nameLen - 1)]
		fourth_letter = name[nameLen - 1]
		fifth_letter = surname[0]
		sixth_letter = surname[random.randint(1, surLen - 1)]
		seventh_letter = surname[random.randint(1, surLen - 1)]
		eighth_letter = surname[surLen - 1]
		username = first_letter + second_letter + third_letter + fourth_letter + fifth_letter + sixth_letter + seventh_letter + eighth_letter
		originalRefPrefArr = ['Animals', 'Food', 'Movies', 'Music', 'Sports']
		refPrefArr = originalRefPrefArr
		randLoop = random.randint(1, 5)
		loop = 0
		leloop = 0
		perPrefArr = [{} for i in range(randLoop)]
		while (loop < randLoop):
			listLen = len(refPrefArr)
			perPrefArr[leloop] = refPrefArr[random.randint(0, listLen - 1)]
			refPrefArr.remove(perPrefArr[leloop])
			leloop += 1
			loop += 1
		age = random.randint(18, 80)
		birthYear = 2020 - age
		randServ = ['gmail', 'hotmail', 'yahoo', 'outlook']
		randThing = ['.co.za', '.com', '.org', '.gov.za', '.net']
		email = name + username + '@' + randServ[random.randint(0, 3)] + randThing[random.randint(0, 4)]
		locationArr = [
			'Albertville, Gauteng',
			'Albertskroon, Gauteng',
			'Aldara Park, Gauteng',
			'Amalgam, Gauteng',
			'Auckland Park, Gauteng',
			'Berario, Gauteng',
			'Beverley Gardens, Gauteng',
			'Blackheath, Gauteng',
			'Blairgowrie, Gauteng',
			'Bordeaux, Gauteng',
			'Bosmont, Gauteng',
			'Brixton, Gauteng',
			'Bryanbrink, Gauteng',
			'Bryanston West, Gauteng',
			'Clynton, Gauteng',
			'Coronationville, Gauteng',
			'Country Life Park, Gauteng',
			'Cowdray Park, Gauteng',
			'Craighall, Gauteng',
			'Craighall Park, Gauteng',
			'Cramerview, Gauteng',
			'Cresta, Gauteng',
			'Crown, Gauteng',
			'Daniel Brink Park, Gauteng',
			'Darrenwood, Gauteng',
			'Dunkeld West, Gauteng',
			'Dunkeld, Gauteng',
			'Emmarentia, Gauteng',
			'Ferndale, Gauteng',
			'Florida Glen, Gauteng',
			'Fontainebleau, Gauteng',
			'Forest Town, Gauteng',
			'Glenadrienne, Gauteng',
			'Gleniffer, Gauteng',
			'Greenside, Gauteng',
			'Greymont, Gauteng',
			'Hurlingham Gardens, Gauteng',
			'Hurlingham, Gauteng',
			'Hyde Park, Gauteng',
			'Jan Hofmeyer, Gauteng',
			'Kensington B, Gauteng',
			'Linden, Gauteng',
			'Lindfield House, Gauteng',
			'Lyme Park, Gauteng',
			'Malanshof, Gauteng',
			'Melville, Gauteng',
			'Mill Hill, Gauteng',
			'Newlands, Johannesburg, Gauteng',
			'Northcliff, Gauteng',
			'Oerder Park, Gauteng',
			'Osummit, Gauteng',
			'Parkhurst, Gauteng',
			'Parkmore, Gauteng',
			'Parktown North, Gauteng',
			'Parkview, Gauteng',
			'Praegville, Gauteng',
			'President Ridge, Gauteng',
			'Randburg, Gauteng',
			'Randpark, Gauteng',
			'Randpark Ridge, Gauteng',
			'Riverbend, Gauteng',
			'Rosebank, Gauteng',
			'Ruiterhof, Gauteng',
			'Sandhurst, Gauteng',
			'Solridge, Gauteng',
			'Sophiatown, Gauteng',
			'Strijdompark, Gauteng',
			'Total South Africa, Gauteng',
			'Vandia Grove, Gauteng',
			'Vrededorp, Gauteng',
			'Waterval Estate, Randburg, Gauteng',
			'Westbury, Gauteng',
			'Westcliff, Gauteng',
			'Westdene, Gauteng',
			'Willowild, Gauteng'
			]
		location = locationArr[random.randint(0, 74)]
		animals = 0
		food = 0
		movies = 0
		music = 0
		sports = 0
		dud = 0
		while (dud < len(perPrefArr)):
			if (perPrefArr[dud] == 'Animals'):
				animals = 1
			if (perPrefArr[dud] == 'Food'):
				food = 1
			if (perPrefArr[dud] == 'Movies'):
				movies = 1
			if (perPrefArr[dud] == 'Music'):
				music = 1
			if (perPrefArr[dud] == 'Sports'):
				sports = 1
			dud += 1
		animalsQuery = 'yes' if animals == 1 else 'no'
		foodQuery = 'yes' if food == 1 else 'no'
		moviesQuery = 'yes' if movies == 1 else 'no'
		musicQuery = 'yes' if music == 1 else 'no'
		sportsQuery = 'yes' if sports == 1 else 'no'
		popularity = random.randint(0, 100)
		lastSeen = str(date.today())
		query = {'Pref': '1', 'Verify': '1', 'Matches': '', 'Chats' : '', 'NewMessage': False, 'Likes': '', 'Dislikes': '', 'Name': name, 'Surname': surname, 'Age': age, 'Email': email, 'username': username, 'Password': hash_password('Password123!'), 
				'Gender': gender, 'Popularity': popularity, 'Blocked': '', 'ProfileViews': '', 'ProfileLikes': '', 'Suburb': location, 'Postal Code': random.randint(1000, 2999), 'Sexual Orientation': SO, 
				'Bio': 'I am ' + name , 'Animals': animalsQuery, 'Music': musicQuery, 'Sports': sportsQuery, 'Food': foodQuery, 'Movies': moviesQuery, 'Noti': '1', 
				'Images': 'trtvyoxhwtnwcxw1, vxrscllmrvqimvu2, ggzdavmalijyoun3, temeocunmfgvgtx4, nemgggxqfkphbkh5', 'Token' : '', 'ConnectionStatus' : lastSeen}
		col.insert_one(query)
		print(query)
		i += 1
	query = {"username": "Admin", "Password": hash_password("Admin123!"), "Blocked": ""}
	col.insert_one(query)

createUsers()
