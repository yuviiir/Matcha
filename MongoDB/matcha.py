from flask import Flask, render_template, url_for, request, redirect , session
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from bson.objectid import ObjectId
import hashlib, binascii, os, re
from pymongo import MongoClient
from datetime import date
import pymongo, random, string
from pip._vendor import requests

UPLOAD_FOLDER = './static/profile_pictures'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['IMAGE_UPLOADS'] = UPLOAD_FOLDER

cluster = MongoClient("mongodb+srv://matcha:password13@matcha-g1enx.mongodb.net/test?retryWrites=true&w=majority")
db = cluster["Matcha"]
col = db["Users"]
notif = db["Notifications"]
chatsdb = db['Chats']

mail_settings = {
	"MAIL_SERVER": 'smtp.gmail.com',
	"MAIL_PORT": 465,
	"MAIL_USE_TLS": False,
	"MAIL_USE_SSL": True,
	"MAIL_USERNAME": 'matcha13.noreply@gmail.com',
	"MAIL_PASSWORD": 'matcha1313'
}
app.config.update(mail_settings)
mail = Mail(app)
@app.route('/')
def index():
	return render_template('index.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
	if request.method == "GET":
		return render_template('index.html')
	name = request.form['name']
	surname = request.form['surname']
	username = request.form['username']
	email = request.form['email']
	password = request.form['password']
	passrep = request.form['passwordrepeat']
	bday = request.form['bday']
	if (name == '' or surname == '' or username == '' or email == '' or password == '' or passrep == '' or bday == ''):
		return render_template('index.html', error = -2)
	bday2 = re.search("([12]\\d{3}/(0[1-9]|1[0-2])/(0[1-9]|[12]\\d|3[01]))", bday) 
	if bday2:
		today = date.today()
		age = today.year - int(bday[0:4]) - ((today.month, today.day) < (int(bday[5:7]), int(bday[8:10])))
		if age > 17:
			result = col.find_one({"username": username})
			if result == None:
				result = col.find_one({"Email": email})
				if result == None:
					if (re.match("[^@]+@[^@]+\\.[^@]+", email)):
						matches = re.search("(?=^.{8,}$)((?=.*\\d)(?=.*\\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$", password)
						if (matches):
							if password == passrep:
								query = {"Pref": "0", "Verify": "0", "Matches": "", "Chats": "", "NewMessage": False, "Likes": "", "Dislikes": "", "Popularity": 0, "Blocked": "", "ProfileViews": "", "ProfileLikes": "", "ConnectionStatus": "", "Noti": "1", "Images": "", "Name": name, "Surname": surname, "Age": age, "Email": email, "username": username, "Password": hash_password(password)}
								col.insert_one(query)
								msg = Message("Matcha Verification", sender="noreply@matcha.com", recipients=[email])
								msg.body = "Hello {0}!\n\nYou have successfully signed up for Matcha!\nPlease click the link below to verify your account.\n\nhttp://localhost:5000/verify/{0}.\n\nThank you.\n".format(username)
								mail.send(msg)
							else:
								return render_template('index.html', error = 1)
						else:
							return render_template('index.html', error = 4)
					else:
						return render_template('index.html', error = 5)
				else:
					return render_template('index.html', error = 6)
			else:
				return render_template('index.html', error = 7)
		else:
			return render_template('index.html', error = 8)
	else:
		return render_template('index.html', error = 9)
	return render_template('index.html', error = -1)

@app.route('/login', methods=['POST', 'GET'])
def login():
	if request.method == "GET":
		return render_template('index.html')
	username = request.form['username']
	password = request.form['password']
	if (username == '' or password == ''):
		return render_template('index.html', error = -2)
	result = col.find_one({"username": username})
	if result != None:
		for cursor in col.find({"username": username}):
			passwordhash = cursor['Password']
			if username == 'Admin':
				if verify_password(passwordhash, password):
					session['user'] = username
					return redirect(url_for('viewblockedusers'))
				else:
					return render_template('index.html', error = 2)
			pref = cursor['Pref']
			verify = cursor['Verify']
		if verify_password(passwordhash, password):
			if result != None:
				if verify == "1":
					global thing
					thing.hasFilters = False
					thing.hasSort = False
					if pref == "0":
						session['user'] = username
						thing.hasPref = False
						return render_template('preferences.html', username = username)
					else:
						session['user'] = username
						thing.hasPref = True
						return redirect(url_for('home'))
				else:
					return render_template('index.html', error = 10)
			else:
				return render_template('index.html', error = 2)
		else:
			return render_template('index.html', error = 2)
	else:
		return render_template('index.html', error = 3)

@app.route('/logout', methods=['GET'])
def logout():
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	lastSeen = str(date.today())
	col.update_one({"username": session["user"]},{"$set": {'ConnectionStatus': lastSeen } })
	session.pop("user", None)
	return redirect(url_for('index'))
		
@app.route('/home', methods=['GET', 'POST'])
def home():
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')
	thing.noti = 'False' + username
	username = session['user']
	col.update_one({"username": username},{"$set": {'ConnectionStatus': 'Online'} })
	query = {"username": username}
	user = col.find_one(query)
	q = {"username": session['user']}
	dat = notif.find(q)
	data = []
	num = 0
	for x in dat:
		data.append(x)
		if x['status'] == "0":
			num += 1
	if (user):
		Food = user['Food']
		Music = user['Music']
		Movies = user['Movies']
		Animals = user['Animals']
		Sports = user['Sports']
		Gender = user['Gender']
		Sexual_Orientation = user['Sexual Orientation']
		Likes = user['Likes']
		Dislikes = user['Dislikes']
		Blocked = user['Blocked']
		Suburb = user['Suburb']
		newMessage = user['NewMessage']
	likesArr = Likes.split(", ")
	dislikesArr = Dislikes.split(", ")
	blockedArr = Blocked.split(", ")
	if request.method == 'POST':
		typeof = request.form['typeOf']
		if typeof == 'search':
			thing.hasFilters = True
			thing.minAge = int(request.form['searchByAgeMin']) if request.form['searchByAgeMin'] != '' else 18
			thing.maxAge = int(request.form['searchByAgeMax']) if request.form['searchByAgeMax'] != '' else 100
			thing.maxAgeValue = int(request.form['searchByAgeMin']) if request.form['searchByAgeMin'] != '' else ''
			thing.maxAgeValue = int(request.form['searchByAgeMax']) if request.form['searchByAgeMax'] != '' else ''
			thing.minPopularity = int(request.form['searchByPopularityMin']) if request.form['searchByPopularityMin'] != '' else -2147483648
			thing.maxPopularity = int(request.form['searchByPopularityMax']) if request.form['searchByPopularityMax'] != '' else 2147483647
			thing.minPopularityValue = int(request.form['searchByPopularityMin']) if request.form['searchByPopularityMin'] != '' else ''
			thing.maxPopularityValue = int(request.form['searchByPopularityMax']) if request.form['searchByPopularityMax'] != '' else ''
			thing.tagAnimals = request.form['animals']
			thing.tagFood = request.form['food']
			thing.tagSports = request.form['sports']
			thing.tagMovies = request.form['movies']
			thing.tagMusic = request.form['music']
			thing.tagAny = request.form['any']
			thing.tagAnimalsCheck = 'checked' if request.form['animals'] == 'yes' else 'no'
			thing.tagFoodCheck = 'checked' if request.form['food'] == 'yes' else 'no'
			thing.tagSportsCheck = 'checked' if request.form['sports'] == 'yes' else 'no'
			thing.tagMoviesCheck = 'checked' if request.form['movies'] == 'yes' else 'no'
			thing.tagMusicCheck = 'checked' if request.form['music'] == 'yes' else 'no'
			thing.tagAnyCheck = 'checked' if request.form['any'] == 'yes' else 'no'
			if (thing.tagAny == 'yes'):
				thing.hasTags = False
			else:
				thing.hasTags = True
			thing.suburb = request.form['searchByLocation'] if request.form['searchByLocation'] != '' else Suburb
			thing.suburbValue = request.form['searchByLocation'] if request.form['searchByLocation'] != '' else ''
		elif typeof == 'sort':
			thing.hasSort = True
			sortby = request.form['sort']
			thing.sortByValue = int(sortby[0] + sortby[1])
			sortby = sortby[2:]
			thing.sortBy = sortby if sortby else None
	if thing.hasFilters == False:
		thing.minAge = 18
		thing.maxAge = 100
		thing.minPopularity = -2147483648
		thing.maxPopularity = 2147483647
		thing.tagAnimalsCheck = 'unchecked'
		thing.tagFoodCheck = 'unchecked'
		thing.tagSportsCheck = 'unchecked'
		thing.tagMoviesCheck = 'unchecked'
		thing.tagMusicCheck = 'unchecked'
		thing.tagAnyCheck = 'checked'
		thing.hasTags = False
		thing.tagAnimals = "no"
		thing.tagFood = "no"
		thing.tagSports = "no"
		thing.tagMovies = "no"
		thing.tagMusic = "no"
		thing.suburb = Suburb
	if thing.hasSort == False:
		thing.sortBy = 'Popularity'
		thing.sortByValue = -1
	query = {"$and" : [
		{ "username" : {"$ne" : username}},
		{ "$or" : [ { "Sports" : Sports }, { "Food" : Food }, { "Music" : Music }, { "Movies" : Movies }, { "Animals" : Animals } ] }
	]}
	if Sexual_Orientation == 'homosexual' and Gender == 'male':
		query["$and"].append({"$or" : [
			{"$and" : [ {"Gender": "male"}, {"Sexual Orientation" : "homosexual"}]},
			{"$and" : [ {"Gender": "male"}, {"Sexual Orientation" : "bisexual"} ]}
			]
		})
	elif Sexual_Orientation == 'heterosexual' and Gender == 'male':
		query["$and"].append({"$or" : [
			{"$and" : [{"Gender": "female"}, {"Sexual Orientation" : "heterosexual"}]},
			{"$and" : [{"Gender": "female"}, {"Sexual Orientation" : "bisexual"}]}
			]
		})
	elif Sexual_Orientation == 'bisexual' and Gender == 'male':
		query["$and"].append({"$or" : [
			{ "$and" : [{"Gender": "male"}, {"Sexual Orientation" : "homosexual"}]},
			{ "$and" : [{"Gender": "female"}, {"Sexual Orientation" : "heterosexual"}]},
			{"Sexual Orientation" : "bisexual"}
			]
		})
	elif Sexual_Orientation == 'homosexual' and Gender == 'female':
		query["$and"].append({"$or" : [
			{"$and" : [{"Gender": "female"}, {"Sexual Orientation" : "homosexual"}]},
			{"$and" : [{"Gender": "female"}, {"Sexual Orientation" : "bisexual"}]}
		]
		})
	elif Sexual_Orientation == 'heterosexual' and Gender == 'female':
		query["$and"].append({"$or" : [
			{"$and" : [{"Gender": "male"}, {"Sexual Orientation" : "heterosexual"}]},
			{"$and" : [{"Gender": "male"}, {"Sexual Orientation" : "bisexual"}]}
			]
		})
	elif Sexual_Orientation == 'bisexual' and Gender == 'female':
		query["$and"].append({"$or" : [
			{ "$and" : [{"Gender": "female"}, {"Sexual Orientation" : "homosexual"}]},
			{ "$and" : [{"Gender": "male"}, {"Sexual Orientation" : "heterosexual"}]},
			{"Sexual Orientation" : "bisexual"}
		]
		})
	compatibleUsers = col.find(query).sort(thing.sortBy, thing.sortByValue)
	compatibleUsersArr = []
	commonTagsArr = []
	commonTags = 0
	tagsArr = ['Movies', 'Food', 'Music', 'Animals', 'Sports']
	if (compatibleUsers):
		for compatibleUser in compatibleUsers:
			if (thing.hasFilters == False and thing.hasSort == False):
				if (compatibleUser['username'] not in likesArr and compatibleUser['username'] not in dislikesArr and
				compatibleUser['username'] not in blockedArr and compatibleUser['Suburb'].upper() == thing.suburb.upper()):
					for tag in tagsArr:
						if (user[tag] == compatibleUser[tag]):
							commonTags += 1
					if (commonTagsArr):
						if (commonTags >= commonTagsArr[0]):
							commonTagsArr.insert(0, commonTags)
							compatibleUsersArr.insert(0, compatibleUser)
						else:
							compatibleUsersArr.append(compatibleUser)
							commonTagsArr.append(commonTags)
					else:
						compatibleUsersArr.append(compatibleUser)
						commonTagsArr.append(commonTags)
					commonTags = 0
			elif (thing.hasTags == False and compatibleUser['username'] not in likesArr and compatibleUser['username'] not in dislikesArr and
				compatibleUser['username'] not in blockedArr and 
				int(compatibleUser['Age']) >= thing.minAge and int(compatibleUser['Age']) <= thing.maxAge and
				int(compatibleUser['Popularity']) >= thing.minPopularity and int(compatibleUser['Popularity']) <= thing.maxPopularity and
				compatibleUser['Suburb'].upper() == thing.suburb.upper()):
					compatibleUsersArr.append(compatibleUser)
			elif (compatibleUser['username'] not in likesArr and compatibleUser['username'] not in dislikesArr and
				compatibleUser['username'] not in blockedArr and 
				int(compatibleUser['Age']) >= thing.minAge and int(compatibleUser['Age']) <= thing.maxAge and
				int(compatibleUser['Popularity']) >= thing.minPopularity and int(compatibleUser['Popularity']) <= thing.maxPopularity and
				compatibleUser['Food'] == thing.tagFood and compatibleUser['Music'] == thing.tagMusic and
				compatibleUser['Movies'] == thing.tagMovies and compatibleUser['Animals'] == thing.tagAnimals and
				compatibleUser['Sports'] == thing.tagSports and compatibleUser['Suburb'].upper() == thing.suburb.upper()):
					compatibleUsersArr.append(compatibleUser)
		if (compatibleUsersArr):
			for compatibleUser in compatibleUsersArr:
				compatibleUser['Images'] = compatibleUser['Images'].split(", ")
			return render_template('home.html', thing=thing, user=session['user'], compatibleUsersArr=compatibleUsersArr, num=num, nomatches=0, newMessage=newMessage )
	return render_template('home.html', thing=thing, nomatches=1, user=session['user'], num=num, newMessage=newMessage)

@app.route('/like<string:likedUser>')
def like(likedUser):
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')
	query = ({"username": likedUser})
	compatibleUser = col.find_one(query)
	if (compatibleUser == None):
		return redirect(url_for('home'))
	compatibleUserPopularity = (int(compatibleUser['Popularity']) + 1) 
	compatibleUserLikes = compatibleUser['Likes']
	compatibleUserLikesArr = compatibleUserLikes.split(', ')
	compatibleUserMatches = compatibleUser['Matches']
	compatibleUserchats = compatibleUser['Chats']
	query = ({"username": session['user']})
	user = col.find_one(query)
	userMatches = user['Matches']
	userLikes = user['Likes']
	chats = user['Chats']
	userProfileLikes = compatibleUser['ProfileLikes']
	userProfileLikes = session['user'] if userProfileLikes == "" else userProfileLikes + ', ' + session['user']
	if (session['user'] in compatibleUserLikesArr):
		compatibleUserMatches = session['user'] if compatibleUserMatches == "" else compatibleUserMatches + ', ' + session['user']
		userMatches = likedUser if userMatches == "" else userMatches + ', ' + likedUser
		chats = compatibleUser['username'] if chats == "" else chats + ', ' + compatibleUser['username']
		compatibleUserchats = user['username'] if compatibleUserchats == "" else compatibleUserchats + ', ' + user['username']
		userLikes = likedUser if userLikes == "" else userLikes + ', ' + likedUser
		query = { "$set": {'Matches': userMatches, 'Likes': userLikes, 'Chats': chats}}
		col.update_one({ "username": session['user'] }, query)
		query = { "$set": {'Matches': compatibleUserMatches, 'Chats': compatibleUserchats}}
		col.update_one({ "username": likedUser }, query)
		q = { "username": likedUser, "Subject": "You Got A Match :)","content":"Congratulations "+ likedUser + ", You just got a match, "+session['user'] +" just liked you back. You can now chat with them!!!","status": "0" }
		q1 = { "username": likedUser }
		ud = col.find(q1)
		a = []
		for x in ud:
			a.append(x)
		if a[0]['Noti'] == "1":
			notif.insert_one(q)
	else:
		userLikes = likedUser if userLikes == "" else userLikes + ', ' + likedUser
		query = { "$set": {'Likes': userLikes}}
		col.update_one({ "username": session['user'] }, query)
		q = { "username": likedUser, "Subject": "Somebody Likes You :)","content":"Congratulations "+ likedUser + ", "+session['user'] +" just liked you!!! View their profile, maybe you will like them back ;)","status": "0" }
		q1 = {"username": likedUser}
		ud = col.find(q1)
		a = []
		for x in ud:
			a.append(x)
		if a[0]['Noti'] == "1":
			notif.insert_one(q)
	query = { "$set": { 'Popularity': compatibleUserPopularity, 'ProfileLikes': userProfileLikes }}
	col.update_one({ "username": likedUser }, query)
	return redirect(url_for('home'))
	

@app.route('/dislike<string:dislikedUser>')
def dislike(dislikedUser):
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')
	query = ({"username": dislikedUser})
	compatibleUser = col.find_one(query)
	if (compatibleUser == None):
		return redirect(url_for('home'))
	query = ({"username": session['user']})
	user = col.find_one(query)
	userDislikes = user['Dislikes']
	q = { "username": dislikedUser, "Subject": "Somebody Just Disliked Your Profile :(","content":"Oh No "+ dislikedUser + "!!!!!!! :( "+ session['user'] + " just disliked your profile!!! But dont worry, theres plenty of fish in the sea ;)","status": "0" }
	q1 = {"username": dislikedUser}
	ud = col.find(q1)
	a = []
	for x in ud:
		a.append(x)
	if a[0]['Noti'] == "1":
		notif.insert_one(q)
	query = ({"username": dislikedUser})
	user = col.find_one(query)
	userPopularity = (int(user['Popularity']) - 1)
	userDislikes = dislikedUser if userDislikes == '' else userDislikes + ', ' + dislikedUser
	query = { "$set": {'Dislikes': userDislikes}}
	col.update_one({ "username": session['user'] }, query)
	query = { "$set": {'Popularity': userPopularity }}
	col.update_one({ "username": dislikedUser }, query)
	return redirect(url_for('home'))

@app.route('/block<string:blockedUser>')
def block(blockedUser):
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')
	query = ({"username": blockedUser})
	compatibleUser = col.find_one(query)
	if (compatibleUser == None):
		return redirect(url_for('home'))
	query = ({"username": session['user']})
	user = col.find_one(query)
	userBlocked = user['Blocked']
	userBlocked = blockedUser if userBlocked == '' else userBlocked + ', ' + blockedUser
	query = { "$set": {'Blocked': userBlocked }}
	col.update_one({ "username": session['user'] }, query)
	col.update_one({ "username": "Admin" }, query )
	return redirect(url_for('home'))

@app.route('/unblock<string:blockedUser>')
def unblock(blockedUser):
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')
	query = ({"username": session['user']})
	user = col.find_one(query)
	userBlocked = user['Blocked']
	userBlockedArr = userBlocked.split(", ")
	userBlockedArr = userBlockedArr.remove(blockedUser)
	userBlocked = "" if userBlockedArr == None else ", ".join(userBlockedArr)
	query = { "$set": {'Blocked': userBlocked }}
	col.update_one({ "username": session['user'] }, query)
	col.update_one({ "username": "Admin" }, query )
	return redirect(url_for('home'))

@app.route('/viewblockedusers')
def viewblockedusers():
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if (username != "Admin"):
		return redirect(url_for('home'))
	query = ({"username": username})
	user = col.find_one(query)
	blockedUsers = user['Blocked']
	blockedUsersArr = blockedUsers.split(', ')
	return render_template('blocked-users.html', blockedUsersArr=blockedUsersArr)

@app.route('/matches')
def matches():
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')
	thing.noti = 'False' + username
	query = ({"username": session['user']})
	user = col.find_one(query)
	matches = user['Matches']
	newMessage = user['NewMessage']
	matches = matches.split(', ')
	q = {"username": session['user']}
	dat = notif.find(q)
	data = []
	num = 0
	for x in dat:
		data.append(x)
		if x['status'] == "0":
			num += 1
	return render_template('matches.html', matches=matches, user=session['user'], num=num, NewMessage=newMessage)

@app.route('/notifications')
def notifications():
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')
	thing.noti = 'False' + username
	q = {"username": session['user']}
	dat = notif.find(q)
	data = []
	for x in dat:
		data.append(x)
	data.reverse()
	myquery = {"username": session['user']}
	newvalues = {"$set": { "status": "1" }}
	notif.update_many(myquery, newvalues)
	query = ({"username": session['user']})
	user = col.find_one(query)
	newMessage = user['NewMessage']
	return render_template('notifications.html', data=data, user=session['user'], NewMessage=newMessage)

@app.route('/notis')
def thing():
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')
	usr = session['user']
	q1 = { "username": usr }
	n = "0"
	for cursor in col.find(q1):
		Name = cursor['Name']
		Surname = cursor['Surname']
		Food = cursor['Food']
		Music = cursor['Music']
		Movies = cursor['Movies']
		Animals = cursor['Animals']
		Sports = cursor['Sports']
		Bio = cursor['Bio']
		Suburb = cursor['Suburb']
		Gender = cursor['Gender']
		Postal_Code = cursor['Postal Code']
		Sexual_Orientation = cursor['Sexual Orientation']
		Noti = cursor['Noti']
	if Noti == "0":
		n = "1"
	nv = { "$set": { "Noti": n } }
	col.update_one(q1, nv)
	return redirect(url_for('profile'))

@app.route('/preferences', methods=['POST'])
def preferences_handler():
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	name = request.form['name']
	surname = request.form['surname']
	gender = request.form['gender']
	sexual = request.form['sexual']
	bio = request.form['bio']
	animals = request.form['animals']
	music = request.form['music']
	movies = request.form['movies']
	sports = request.form['sports']
	food = request.form['food']
	uploaded_images = request.files.getlist('img')
	index = 0
	suburb = request.form['suburb']
	postal_code = request.form['postal']
	for file in uploaded_images:
		index += 1
		if (index == 1):
			imgName = randomString(15) + str(index)
		else:
			imgName =  imgName + ", " + randomString(15) + str(index)
	if index > 5:
		return render_template('preferences.html', error=1)
	imgNameArray = imgName.split(', ')
	for file in uploaded_images:
		index -= 1
		file.save(os.path.join(app.config['IMAGE_UPLOADS'], imgNameArray[index] + ".png"))
	myquery = { "username": username }
	newvalues = { "$set": {"Pref": "1", "Name": name, "Surname": surname, "Gender": gender, "Suburb": suburb, "Postal Code": postal_code, "Sexual Orientation": sexual, "Bio": bio, "Images": imgName, "Animals": animals, "Music": music, "Sports": sports, "Food": food, "Movies": movies} }
	col.update_one(myquery, newvalues)
	thing.hasPref = True
	return redirect(url_for('home'))

@app.route('/editprofile')
def editprofile():
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')
	return render_template('preferences.html', username = username)

@app.route('/profile')
def profile():
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')
	thing.noti = 'False' + username
	query = {"username": username}
	for cursor in col.find(query):
		Name = cursor['Name']
		Surname = cursor['Surname']
		Food = cursor['Food']
		Music = cursor['Music']
		Movies = cursor['Movies']
		Animals = cursor['Animals']
		Sports = cursor['Sports']
		Bio = cursor['Bio']
		Suburb = cursor['Suburb']
		Gender = cursor['Gender']
		Postal_Code = cursor['Postal Code']
		Sexual_Orientation = cursor['Sexual Orientation']
		Noti = cursor['Noti']
		Image_Name_Arr = cursor['Images'].split(', ')
		Popularity = cursor['Popularity']
		Age = cursor['Age']
		newMessage = cursor['NewMessage']
	q = {"username": session['user']}
	dat = notif.find(q)
	data = []
	num = 0
	for x in dat:
		data.append(x)
		if x['status'] == "0":
			num += 1
	return render_template('profile.html', user=username, age=Age, name=Name, surname=Surname, food=Food, music=Music, movies=Movies, animals=Animals, sports=Sports, bio=Bio, suburb=Suburb, gender=Gender, postal_code=Postal_Code, sexual_orientation=Sexual_Orientation, ImgArr=Image_Name_Arr, noti=Noti, popularity=Popularity,num=num, NewMessage=newMessage)

@app.route('/viewprofile/<username>')
def viewprofile(username):
	try:
		username1 = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')
	query = ({"username": username})
	compatibleUser = col.find_one(query)
	if (compatibleUser == None):
		return redirect(url_for('home'))	
	query = {"username": username}
	for cursor in col.find(query):
		Name = cursor['Name']
		Surname = cursor['Surname']
		Food = cursor['Food']
		Music = cursor['Music']
		Movies = cursor['Movies']
		Animals = cursor['Animals']
		Sports = cursor['Sports']
		Bio = cursor['Bio']
		Suburb = cursor['Suburb']
		Gender = cursor['Gender']
		Postal_Code = cursor['Postal Code']
		Sexual_Orientation = cursor['Sexual Orientation']
		Noti = cursor['Noti']
		userProfileViews = cursor['ProfileViews']
		Image_Name_Arr = cursor['Images'].split(', ')
		ConnectionStatus = cursor['ConnectionStatus']
		Popularity = cursor['Popularity']
		Age = cursor['Age']
		newMessage = cursor['NewMessage']
	chatee = col.find_one(query)
	query = { "username": session['user'] }
	user = col.find_one(query)
	chatter = user
	blockedUsers = user['Blocked']
	blockedUsers = blockedUsers.split(', ')
	if (username in blockedUsers):
		blocked = 1
	else:
		blocked = 0
	userProfileViewsArr = userProfileViews.split(', ')
	if (session['user'] not in userProfileViewsArr):
		userProfileViews = session['user'] if userProfileViews == "" else userProfileViews + ', ' + session['user']
		query = { "$set": {'ProfileViews': userProfileViews}}
		col.update_one({ "username": username }, query)
	if (thing.noti == 'False' + username1):
		thing.noti = 'True' + username1
		q = { "username": username, "Subject": "Somebody Viewed Your Profile :)","content":"Hey There "+ username + ","+session['user'] +" is currently viewing your profile!!!","status": "0" }
		notif.insert_one(q)
	q = {"username": session['user']}
	dat = notif.find(q)
	data = []
	num = 0
	for x in dat:
		data.append(x)
		if x['status'] == "0":
			num += 1
	return render_template('view-profile.html', blocked=blocked, user=session['user'], username=username, age=Age, name=Name, surname=Surname, food=Food, music=Music, movies=Movies, animals=Animals, sports=Sports, bio=Bio, suburb=Suburb, gender=Gender, postal_code=Postal_Code, sexual_orientation=Sexual_Orientation,  noti=Noti, ImgArr=Image_Name_Arr, connectionStatus=ConnectionStatus, popularity=Popularity,num=num, NewMessage=newMessage)


@app.route('/chat/<chatUser>', methods=['GET', 'POST'])
def chat(chatUser):
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')	
	if request.method == 'POST' :
		message = request.form['message']
		query = { "FromUser" : username, "ToUser" : chatUser, 'Message': message, 'Read': False }
		chatsdb.insert_one(query)
		query = {"$set": {"NewMessage": True}}
		col.update_one({"username": chatUser}, query)
	query = {'username': session['user']}
	user = col.find_one(query)
	matches = user['Matches'].split(', ')
	if (chatUser not in matches):
		return redirect(url_for('chats'))
	query = {"$or" : [
		{ "$and" : [ { "FromUser" : chatUser }, { "ToUser" : username }]},
		{ "$and" : [ { "FromUser" : username }, { "ToUser" : chatUser }]}]}
	chatMessages = chatsdb.find(query)
	chatMess = []
	newMessage = False
	for chatMessage in chatMessages:
		if chatMessage['Read'] == False and chatMessage['ToUser'] == username:
			newMessage = True
		if chatMessage['ToUser'] == username:
			query = {"$set": {"Read": True}}
			chatsdb.update_many({"ToUser": username}, query)
			query = {"$set": {"NewMessage": False}}
			col.update_one({"username": username}, query)
		chatMess.append(chatMessage)
	q = {"username": session['user']}
	dat = notif.find(q)
	data = []
	num = 0
	for x in dat:
		data.append(x)
		if x['status'] == "0":
			num += 1
	return render_template('chat.html', chatMessages=chatMess, chatUser=chatUser, newMessage=newMessage, user=username, num=num)
	
@app.route('/chats')
def chats():
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')	
	thing.noti = 'False' + username
	username = session['user']
	query = {"username": username}
	user = col.find_one(query)
	chats = user['Chats']
	newMessage = user['NewMessage']
	chats = chats.split(', ')
	q = {"username": session['user']}
	dat = notif.find(q)
	data = []
	num = 0
	for x in dat:
		data.append(x)
		if x['status'] == "0":
			num += 1
	return render_template('chats.html', chats=chats, newMessage=newMessage, user=username, num=num)

@app.route('/profileviews/')
def profileviews():
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')	
	thing.noti = 'False' + username
	query = ({"username": username})
	user = col.find_one(query)
	profileViews = user['ProfileViews']
	newMessage = user['NewMessage']
	profileViews = profileViews.split(', ')
	q = {"username": session['user']}
	dat = notif.find(q)
	data = []
	num = 0
	for x in dat:
		data.append(x)
		if x['status'] == "0":
			num += 1
	return render_template('profile-views.html', profileViews=profileViews, user=session['user'],num=num, NewMessage=newMessage)

@app.route('/profilelikes/')
def profilelikes():
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')	
	thing.noti = 'False' + username
	query = ({"username": username})
	user = col.find_one(query)
	profileLikes = user['ProfileLikes']
	profileLikes = profileLikes.split(', ')
	q = {"username": session['user']}
	dat = notif.find(q)
	data = []
	num = 0
	for x in dat:
		data.append(x)
		if x['status'] == "0":
			num += 1
	return render_template('profile-likes.html', profileLikes=profileLikes, user=session['user'],num=num)

@app.route('/verify/<username>', methods=['POST', 'GET'])
def verify(username):
		query = ({"username": username})
		compatibleUser = col.find_one(query)
		if (compatibleUser == None or compatibleUser['Verify'] == 1 ):
			return redirect(url_for('index'))
		myquery = { "username": username }
		newvalues = { "$set": {"Verify": "1"} }
		col.update_one(myquery, newvalues)
		return render_template('index.html', verified=1)

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
	if (request.method == 'GET'):
		reset = 0
		err = ''
		return render_template('reset_password.html', err=err, reset=reset)
	if (request.method == 'POST'):
		reset = 0
		err = ''
		email = request.form['email']
		if (len(email) > 0):
			emailCheck = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
			if (re.search(emailCheck, email)):
				findExisting = { 'Email' : email }
				result = col.find_one(findExisting)
				if (result == None):
					err = 3
					return render_template('reset_password.html', err=err, reset=reset)
				else:
					err = 0
					token = hash_password(email)
					oldToken = { 'Email' : email }
					newToken = { '$set': { 'Token' : token } }
					res = col.update_one(oldToken, newToken)
					msg = Message("Matcha Password Reset", sender="noreply@matcha.com", recipients=[email])
					msg.body = "Hello!\n\nYou have requested a password reset. Please click the link below to verify your account and reset your password.\n\nhttp://127.0.0.1:5000/reset?email={0}&token={1}.\n\nThank you.\n".format(email, token)
					mail.send(msg)
					return render_template('reset_password.html', err=err, reset=reset)
			elif not (re.search(emailCheck, email)):
				err = 1
				return render_template('reset_password.html', err=err, reset=reset)
		else :
			err = 2
			return render_template('reset_password.html', err=err, reset=reset)

@app.route('/reset', methods=['GET', 'POST'])
def reset():
	if (request.method == 'GET'):
		err = ''
		reset = 1
		email = request.args.get('email')
		token = request.args.get('token')
		emailQuery = {'Email' : email}
		tokenQuery = {'Token' : token}
		validEmail = col.find_one(emailQuery)
		validToken = col.find_one(tokenQuery)
		if (validEmail == None or validToken == None):
			err = 4
			return render_template('reset_password.html', err=err, reset=reset)
		else:
			err = 5
			return render_template('reset_password.html', err=err, reset=reset)
	if (request.method == 'POST'):
		err = ''
		reset = 1
		email = request.form['email']
		password = request.form['newPassword']
		confirmPassword = request.form['confirmNewPassword']
		matches = re.search("(?=^.{8,}$)((?=.*\\d)(?=.*\\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$", password)
		if (matches):
			if (password == confirmPassword):
				err = 6
				oldPassword = { 'Email' : email }
				newPassword = { '$set': { 'Token' : '' , 'Password' : hash_password(password)} }
				res = col.update_one(oldPassword, newPassword)
				return redirect(url_for('index'))
			else:
				err = 7
				return render_template('index.html', err=err, reset=reset)
		else:
			err = 8
			return render_template('index.html', err=err, reset=reset)
		return render_template('index.html', err=err, reset=reset)

def hash_password(password):
	salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
	pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
	pwdhash = binascii.hexlify(pwdhash)
	return (salt + pwdhash).decode('ascii')

def verify_password(stored_password, provided_password):
	salt = stored_password[:64]
	stored_password = stored_password[64:]
	pwdhash = hashlib.pbkdf2_hmac('sha512', provided_password.encode('utf-8'), str(salt).encode('ascii'), 100000)
	pwdhash = binascii.hexlify(pwdhash).decode('ascii')
	return pwdhash == stored_password

def randomString(stringLength=8):
	letters = string.ascii_lowercase
	return ''.join(random.choice(letters) for i in range(stringLength))

if (__name__ == "__main__"):
	app.run(debug = True)