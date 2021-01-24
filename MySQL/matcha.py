from flask import Flask, render_template, url_for, request, redirect , session
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from bson.objectid import ObjectId
import hashlib, binascii, os, re
from pymongo import MongoClient
from datetime import date
import pymongo, random, string
from pip._vendor import requests
from mysql.connector import errors

UPLOAD_FOLDER = './static/profile_pictures'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['IMAGE_UPLOADS'] = UPLOAD_FOLDER

from setup import create_conn
from setup import close_conn

db = create_conn()
cursor = db.cursor()
cursor.execute("USE matcha_sql")



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
	db = create_conn()
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
			sql = "SELECT * FROM users WHERE username = %s"
			cursor.execute(sql, (username, ))
			result = cursor.fetchall()
			print(result)
			if result == []:
				sql = "SELECT * FROM users WHERE email = %s"
				cursor.execute(sql, (email,))
				result = cursor.fetchall()
				if result == []:
					if (re.match("[^@]+@[^@]+\\.[^@]+", email)):
						matches = re.search("(?=^.{8,}$)((?=.*\\d)(?=.*\\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$", password)
						if (matches):
							if password == passrep:
								sql = ("INSERT INTO users (Pref, Verify, Matches, Chats, NewMessage, Likes, Dislikes,"
								"Popularity, Blocked, ProfileViews, ProfileLikes, ConnectionStatus, Noti, Images,"
								"Name, Surname, Age, Email, username, Password) VALUES ('0', '1', '', '', 'False', '', '', 0,"
								"'', '', '', '', '1', '', %s, %s, %s, %s, %s, %s)")
								cursor.execute(sql, (name, surname, age, email, username, hash_password(password)))
								db.commit()
								db = close_conn(db)
								# msg = Message("Matcha Verification", sender="noreply@matcha.com", recipients=[email])
								# msg.body = "Hello {0}!\n\nYou have successfully signed up for Matcha!\nPlease click the link below to verify your account.\n\nhttp://localhost:5000/verify/{0}.\n\nThank you.\n".format(username)
								# mail.send(msg)
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
	db = create_conn()
	if request.method == "GET":
		return render_template('index.html')
	username = request.form['username']
	password = request.form['password']
	if (username == '' or password == ''):
		return render_template('index.html', error = -2)
	sql = "SELECT * FROM users WHERE username = %s"
	cursor.execute(sql, (username, ))
	result = cursor.fetchall()
	db = close_conn(db)
	if result != []:
		passwordhash = result[0][13]
		if username == 'Admin':
			if verify_password(passwordhash, password):
				session['user'] = username
				return redirect(url_for('viewblockedusers'))
			else:
				return render_template('index.html', error = 2)
		pref = result[0][1]
		verify = result[0][2]
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
	db = create_conn()
	lastSeen = str(date.today())
	sql = "UPDATE users SET ConnectionStatus = %s WHERE username = %s"
	cursor.execute(sql, (lastSeen, session["user"]))
	db.commit()
	session.pop("user", None)
	db = close_conn(db)
	return redirect(url_for('index'))

@app.route('/home', methods=['GET', 'POST'])
def home():
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')
	db = create_conn()
	thing.noti = 'False' + username
	username = session['user']
	sql = "UPDATE users SET ConnectionStatus = %s WHERE username = %s"
	cursor.execute(sql, ('Online', session["user"]))
	db.commit()
	sql = "SELECT * FROM users WHERE username = %s"
	cursor.execute(sql, (username, ))
	user = cursor.fetchall()
	user = user[0]
	sql = "SELECT * FROM notifications WHERE username = %s"
	cursor.execute(sql, (session['user'], ))
	dat = cursor.fetchall()
	data = []
	num = 0
	for x in dat:
		data.append(x)
		if x[2] == "0":
			num += 1
	if (user):
		newMessage = True if user[5] == "True" else False
		Likes = user[6]
		Dislikes = user[7]
		Gender = user[14]
		Blocked = user[16]
		Suburb = user[19]
		Sexual_Orientation = user[21]
		Animals = user[23]
		Music = user[24]
		Sports = user[25]
		Food = user[26]
		Movies = user[27]
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
			thing.sortByValue = "DESC" if int(sortby[0] + sortby[1]) == -1 else "ASC"
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
		thing.sortByValue = "DESC"
	sql = "SELECT * FROM users WHERE username != %s AND (Sports = %s OR Music = %s OR Food = %s OR Movies = %s OR Animals = %s)"
	if Sexual_Orientation == 'homosexual' and Gender == 'male':
		sql = sql + " AND ((Gender = 'male' AND `Sexual Orientation` = 'homosexual') OR (Gender = 'male' AND `Sexual Orientation` = 'bisexual'))"
	elif Sexual_Orientation == 'heterosexual' and Gender == 'male':
		sql = sql + " AND ((Gender = 'female' AND `Sexual Orientation` = 'heterosexual') OR (Gender = 'female' AND `Sexual Orientation` = 'bisexual'))"
	elif Sexual_Orientation == 'bisexual' and Gender == 'male':
		sql = sql + " AND ((Gender = 'male' AND `Sexual Orientation` = 'homosexual') OR (Gender = 'female' AND `Sexual Orientation` = 'heterosexual') OR (`Sexual Orientation` = 'bisexual'))"
	elif Sexual_Orientation == 'homosexual' and Gender == 'female':
		sql = sql + " AND ((Gender = 'female' AND `Sexual Orientation` = 'homosexual') OR (Gender = 'female' AND `Sexual Orientation` = 'bisexual'))"
	elif Sexual_Orientation == 'heterosexual' and Gender == 'female':
		sql = sql + " AND ((Gender = 'male' AND `Sexual Orientation` = 'heterosexual') OR (Gender = 'male' AND `Sexual Orientation` = 'bisexual'))"
	elif Sexual_Orientation == 'bisexual' and Gender == 'female':
		sql = sql + " AND ((Gender = 'female' AND `Sexual Orientation` = 'homosexual') OR (Gender = 'male' AND `Sexual Orientation` = 'heterosexual') OR (`Sexual Orientation` = 'bisexual'))"
	sql = sql + " ORDER BY %s %s"
	values = (username, Sports, Music, Food, Movies, Animals, thing.sortBy, thing.sortByValue)
	cursor.execute(sql, values)
	compatibleUsers = cursor.fetchall()
	compatibleUsersArr = []
	commonTagsArr = []
	commonTags = 0
	i = 0
	tagsArr = [23, 24, 25, 26, 27]
	db = close_conn(db)
	if (compatibleUsers):
		while(i < len(compatibleUsers)):
			compatibleUser = compatibleUsers[i]
			if (thing.hasFilters == False and thing.hasSort == False):
				if (compatibleUser[12] not in likesArr and compatibleUser[12] not in dislikesArr and
				compatibleUser[12] not in blockedArr and compatibleUser[19].upper() == thing.suburb.upper()):
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
			elif (thing.hasTags == False and compatibleUser[12] not in likesArr and compatibleUser[12] not in dislikesArr and
				compatibleUser[12] not in blockedArr and
				int(compatibleUser[10]) >= thing.minAge and int(compatibleUser[10]) <= thing.maxAge and
				int(compatibleUser[15]) >= thing.minPopularity and int(compatibleUser[15]) <= thing.maxPopularity and
				compatibleUser[19].upper() == thing.suburb.upper()):
					compatibleUsersArr.append(compatibleUser)
			elif (compatibleUser[12] not in likesArr and compatibleUser[12] not in dislikesArr and
				compatibleUser[12] not in blockedArr and
				int(compatibleUser[10]) >= thing.minAge and int(compatibleUser[10]) <= thing.maxAge and
				int(compatibleUser[15]) >= thing.minPopularity and int(compatibleUser[15]) <= thing.maxPopularity and
				compatibleUser[26] == thing.tagFood and compatibleUser[24] == thing.tagMusic and
				compatibleUser[27] == thing.tagMovies and compatibleUser[23] == thing.tagAnimals and
				compatibleUser[25] == thing.tagSports and compatibleUser[19].upper() == thing.suburb.upper()):
					compatibleUsersArr.append(compatibleUser)
			i += 1
		i = 0
		if (compatibleUsersArr):
			while(i < len(compatibleUsersArr)):
				compatibleUser1 = compatibleUsersArr[i]
				images = compatibleUser1[29].split(", ")
				i += 1
			return render_template('home.html', thing=thing, user=session['user'], compatibleUsersArr=compatibleUsersArr, images=images, num=num, nomatches=0, newMessage=newMessage )
	return render_template('home.html', thing=thing, nomatches=1, user=session['user'], num=num, newMessage=newMessage)

@app.route('/like<string:likedUser>')
def like(likedUser):
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')
	db = create_conn()
	sql = "SELECT * FROM users WHERE username = %s"
	cursor.execute(sql, (likedUser, ))
	compatibleUser = cursor.fetchall()
	compatibleUser = compatibleUser[0]
	if (compatibleUser == None):
		return redirect(url_for('home'))
	compatibleUserPopularity = (int(compatibleUser[15]) + 1)
	compatibleUserLikes = compatibleUser[6]
	compatibleUserLikesArr = compatibleUserLikes.split(', ')
	compatibleUserMatches = compatibleUser[3]
	compatibleUserchats = compatibleUser[4]
	sql = "SELECT * FROM users WHERE username = %s"
	cursor.execute(sql, (session['user'], ))
	user = cursor.fetchall()
	user = user[0]
	userMatches = user[3]
	userLikes = user[6]
	chats = user[4]
	userProfileLikes = compatibleUser[18]
	userProfileLikes = session['user'] if userProfileLikes == "" else userProfileLikes + ', ' + session['user']
	if (session['user'] in compatibleUserLikesArr):
		compatibleUserMatches = session['user'] if compatibleUserMatches == "" else compatibleUserMatches + ', ' + session['user']
		userMatches = likedUser if userMatches == "" else userMatches + ', ' + likedUser
		chats = compatibleUser[12] if chats == "" else chats + ', ' + compatibleUser[12]
		compatibleUserchats = user[12] if compatibleUserchats == "" else compatibleUserchats + ', ' + user[12]
		userLikes = likedUser if userLikes == "" else userLikes + ', ' + likedUser
		sql = "UPDATE users SET Matches = %s, Likes = %s, Chats = %s WHERE username = %s"
		cursor.execute(sql, (userMatches, userLikes, chats, session["user"]))
		db.commit()
		sql = "UPDATE users SET Matches = %s, Chats = %s WHERE username = %s"
		cursor.execute(sql, (compatibleUserMatches, compatibleUserchats, likedUser))
		db.commit()
		sql = "SELECT * FROM users WHERE username = %s"
		cursor.execute(sql, (likedUser, ))
		ud = cursor.fetchall()
		a = []
		i = 0
		while(i < len(ud)):
			x = ud[i]
			a.append(x)
			i += 1
		if a[0][28] == "1":
			sql = ("INSERT INTO notifications (username, Subject, content, status)"
			"VALUES (%s, 'You Got A Match :)', %s, '0')")
			cursor.execute(sql, (username, 'Congratulations {} , you just got a match, {} just liked you back. You can now chat with them!!!'.format(likedUser, session['user'])))
			db.commit()
	else:
		userLikes = likedUser if userLikes == "" else userLikes + ', ' + likedUser
		sql = "UPDATE users SET Likes = %s WHERE username = %s"
		cursor.execute(sql, (userLikes, session["user"]))
		db.commit()
		sql = "SELECT * FROM users WHERE username = %s"
		cursor.execute(sql, (likedUser, ))
		ud = cursor.fetchall()
		a = []
		i = 0
		while(i < len(ud)):
			x = ud[i]
			a.append(x)
			i += 1
		if a[0][28] == "1":
			sql = ("INSERT INTO notifications (username, Subject, content, status)"
			"VALUES (%s, 'Somebody Likes You :)', %s, '0')")
			cursor.execute(sql, (username, 'Congratulations {}, {} just liked you!!! View their profile, maybe you will like them back ;)'.format(likedUser, session['user'])))
			db.commit()
	sql = "UPDATE users SET Popularity = %s, ProfileLikes = %s WHERE username = %s"
	cursor.execute(sql, (compatibleUserPopularity, userProfileLikes, likedUser))
	db.commit()
	db = close_conn(db)
	return redirect(url_for('home'))


@app.route('/dislike<string:dislikedUser>')
def dislike(dislikedUser):
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')
	sql = "SELECT * FROM users WHERE username = %s"
	cursor.execute(sql, dislikedUser)
	compatibleUser = cursor.fetchall()
	compatibleUser = compatibleUser[0]
	if (compatibleUser == None):
		return redirect(url_for('home'))
	sql = "SELECT * FROM users WHERE username = %s"
	cursor.execute(sql, (session['user'], ))
	user = cursor.fetchall()
	user = user[0]
	userDislikes = user[7]
	sql = "SELECT * FROM users WHERE username = %s"
	cursor.execute(sql, (dislikedUser, ))
	ud = cursor.fetchall()
	a = []
	i = 0
	while(i < len(ud)):
		x = ud[i]
		a.append(x)
		i += 1
	if a[0][28] == "1":
		sql = ("INSERT INTO notifications (username, Subject, content, status)"
		"VALUES (%s, 'Somebody Just Disliked Your Profile :(', %s, '0')")
		cursor.execute(sql, (username, 'Oh No, {}! {} just disliked your profile!!! But dont worry, theres plenty of fish in the sea ;)'.format(dislikedUser, session['user'])))
		db.commit()
	sql = "SELECT * FROM users WHERE username = %s"
	cursor.execute(sql, (dislikedUser, ))
	user = cursor.fetchall()
	user = user[0]
	userPopularity = (int(user[15]) - 1)
	userDislikes = dislikedUser if userDislikes == '' else userDislikes + ', ' + dislikedUser
	sql = "UPDATE users SET Dislikes = %s WHERE username = %s"
	cursor.execute(sql, (userDislikes, session["user"]))
	sql = "UPDATE users SET Popularity = %s WHERE username = %s"
	cursor.execute(sql, (userPopularity, dislikedUser))
	db.commit()
	return redirect(url_for('home'))

@app.route('/block<string:blockedUser>')
def block(blockedUser):
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')
	db = create_conn()
	sql = "SELECT * FROM users WHERE username = %s"
	cursor.execute(sql, blockedUser)
	compatibleUser = cursor.fetchall()
	compatibleUser = compatibleUser[0]
	if (compatibleUser == None):
		return redirect(url_for('home'))
	sql = "SELECT * FROM users WHERE username = %s"
	cursor.execute(sql, session['user'])
	user = cursor.fetchall()
	user = user[0]
	userBlocked = user[16]
	userBlocked = blockedUser if userBlocked == '' else userBlocked + ', ' + blockedUser
	sql = "UPDATE users SET Blocked = %s WHERE username = %s"
	cursor.execute(sql, (userBlocked, session["user"]))
	cursor.execute(sql, (userBlocked, "Admin"))
	db.commit()
	db = close_conn(db)
	return redirect(url_for('home'))

@app.route('/unblock<string:blockedUser>')
def unblock(blockedUser):
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')
	db = create_conn()
	sql = "SELECT * FROM users WHERE username = %s"
	cursor.execute(sql, session['user'])
	user = cursor.fetchall()
	user = user[0]
	userBlocked = user[16]
	userBlockedArr = userBlocked.split(", ")
	userBlockedArr = userBlockedArr.remove(blockedUser)
	userBlocked = "" if userBlockedArr == None else ", ".join(userBlockedArr)
	sql = "UPDATE users SET Blocked = %s WHERE username = %s"
	cursor.execute(sql, (userBlocked, session["user"]))
	cursor.execute(sql, (userBlocked, "Admin"))
	db.commit()
	db = close_conn(db)
	return redirect(url_for('home'))

@app.route('/viewblockedusers')
def viewblockedusers():
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if (username != "Admin"):
		return redirect(url_for('home'))
	db = create_conn()
	sql = "SELECT * FROM users WHERE username = %s"
	cursor.execute(sql, username)
	user = cursor.fetchall()
	user = user[0]
	blockedUsers = user[16]
	blockedUsersArr = blockedUsers.split(', ')
	db = close_conn(db)
	return render_template('blocked-users.html', blockedUsersArr=blockedUsersArr)

@app.route('/matches')
def matches():
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')
	db = create_conn()
	thing.noti = 'False' + username
	sql = "SELECT * FROM users WHERE username = %s"
	val = (session['user'], )
	cursor.execute(sql, val)
	user = cursor.fetchall()
	user = user[0]
	matches = user[3]
	newMessage = True if user[5] == "True" else False
	matches = matches.split(', ')
	sql = "SELECT * FROM notifications WHERE username = %s"
	val = (session['user'], )
	cursor.execute(sql, val)
	dat = cursor.fetchall()
	data = []
	num = 0
	i = 0
	while(i < len(dat)):
		x = dat[i]
		data.append(x)
		if x[3] == "0":
			num += 1
		i += 1
	db = close_conn(db)
	return render_template('matches.html', matches=matches, user=session['user'], num=num, NewMessage=newMessage)

@app.route('/notifications')
def notifications():
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')
	db = create_conn()
	thing.noti = 'False' + username
	sql = "SELECT * FROM notifications WHERE username = %s"
	cursor.execute(sql, (session['user'], ))
	dat = cursor.fetchall()
	data = []
	i = 0
	while(i < len(dat)):
		x = dat[i]
		data.append(x)
		i += 1
	data.reverse()
	sql = "UPDATE notifications SET status = %s WHERE username = %s"
	cursor.execute(sql, ("1", session['user']))
	db.commit()
	sql = "SELECT * FROM users WHERE username = %s"
	cursor.execute(sql, (session['user'], ))
	user = cursor.fetchall()
	user = user[0]
	newMessage = True if user[5] == "True" else False
	db = close_conn(db)
	return render_template('notifications.html', data=data, user=session['user'], NewMessage=newMessage)

@app.route('/notis')
def thing():
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')
	db = create_conn()
	usr = session['user']
	n = "0"
	sql = "SELECT * FROM users WHERE username = %s"
	cursor.execute(sql, (usr, ))
	dat = cursor.fetchall()
	curs = dat[0]
	Name = curs[8]
	Surname = curs[9]
	Food = curs[26]
	Music = curs[24]
	Movies = curs[26]
	Animals = curs[23]
	Sports = curs[25]
	Bio = curs[22]
	Suburb = curs[19]
	Gender = curs[14]
	Postal_Code = curs[20]
	Sexual_Orientation = curs[21]
	Noti = curs[28]
	if Noti == "0":
		n = "1"
	sql = "UPDATE users SET Noti = %s WHERE username = %s"
	cursor.execute(sql, (n, usr))
	db.commit()
	db = close_conn(db)
	return redirect(url_for('profile'))

@app.route('/preferences', methods=['POST'])
def preferences_handler():
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	db = create_conn()
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
	sql = ("UPDATE users SET `Pref` = %s, `Name` = %s, `Surname` = %s, "
		"`Gender` = %s, `Suburb` = %s, `Postal Code` = %s, `Sexual Orientation` = %s, `Bio` = %s,"
		"`Images` = %s, `Animals` = %s, `Music` = %s, `Sports` = %s, `Food` = %s, `Movies` = %s WHERE username = %s")
	val = ("1", name, surname, gender, suburb, postal_code, sexual, bio, imgName, animals, music, sports, food, movies, session['user'])
	cursor.execute(sql, val)
	db.commit()
	thing.hasPref = True
	db = close_conn(db)
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
	db = create_conn()
	thing.noti = 'False' + username
	sql = "SELECT * FROM users WHERE username = %s"
	cursor.execute(sql, (username, ))
	dat = cursor.fetchall()
	curs = dat[0]
	Name = curs[8]
	Surname = curs[9]
	Food = curs[26]
	Music = curs[24]
	Movies = curs[26]
	Animals = curs[23]
	Sports = curs[25]
	Bio = curs[22]
	Suburb = curs[19]
	Gender = curs[14]
	Postal_Code = curs[20]
	Sexual_Orientation = curs[21]
	Noti = curs[28]
	Image_Name_Arr = curs[29].split(', ')
	Popularity = curs[15]
	Age = curs[10]
	newMessage = True if curs[5] == "True" else False
	sql = "SELECT * FROM notifications WHERE username = %s"
	cursor.execute(sql, (session['user'], ))
	dat = cursor.fetchall()
	data = []
	num = 0
	i = 0
	while(i < len(dat)):
		x = dat[i]
		data.append(x)
		if x[2] == "0":
			num += 1
		i += 1
	db = close_conn(db)
	return render_template('profile.html', user=username, age=Age, name=Name, surname=Surname, food=Food, music=Music, movies=Movies, animals=Animals, sports=Sports, bio=Bio, suburb=Suburb, gender=Gender, postal_code=Postal_Code, sexual_orientation=Sexual_Orientation, ImgArr=Image_Name_Arr, noti=Noti, popularity=Popularity,num=num, NewMessage=newMessage)

@app.route('/viewprofile/<username>')
def viewprofile(username):
	try:
		username1 = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')
	db = create_conn()
	sql = "SELECT * FROM users WHERE username = %s"
	cursor.execute(sql, (username, ))
	compatibleUser = cursor.fetchall()
	if (compatibleUser == None):
		return redirect(url_for('home'))
	sql = "SELECT * FROM users WHERE username = %s"
	cursor.execute(sql, (username, ))
	data = cursor.fetchall()
	curs = data [0]
	Name = curs[8]
	Surname = curs[9]
	Food = curs[26]
	Music = curs[24]
	Movies = curs[26]
	Animals = curs[23]
	Sports = curs[25]
	Bio = curs[22]
	Suburb = curs[19]
	Gender = curs[14]
	Postal_Code = curs[20]
	Sexual_Orientation = curs[21]
	Noti = curs[28]
	userProfileViews = curs[17]
	ConnectionStatus = curs[31]
	Image_Name_Arr = curs[29].split(', ')
	Popularity = curs[15]
	Age = curs[10]
	newMessage = True if curs[5] == "True" else False
	chatee = data
	sql = "SELECT * FROM users WHERE username = %s"
	cursor.execute(sql, (username, ))
	user = cursor.fetchall()
	user = user[0]
	blockedUsers = user[16]
	blockedUsers = blockedUsers.split(', ')
	if (username in blockedUsers):
		blocked = 1
	else:
		blocked = 0
	userProfileViewsArr = userProfileViews.split(', ')
	if (session['user'] not in userProfileViewsArr):
		userProfileViews = session['user'] if userProfileViews == "" else userProfileViews + ', ' + session['user']
		sql = "UPDATE users SET ProfileViews = %s WHERE username = %s"
		cursor.execute(sql, (userProfileViews, username))
		db.commit()
	if (thing.noti == 'False' + username1):
		thing.noti = 'True' + username1
		sql = ("INSERT INTO notifications (username, Subject, content, status) "
		"VALUES (%s, 'Somebody Viewed Your Profile :)', %s, '0')")
		cursor.execute(sql, (username, "Hey There {}! {} is currently viewing your profile!!!".format(username, session['user'])))
		db.commit()
	sql = "SELECT * FROM notifications WHERE username = %s"
	cursor.execute(sql, (session['user'], ))
	dat = cursor.fetchall()
	data = []
	num = 0
	i = 0
	while(i < len(dat)):
		x = dat[i]
		data.append(x)
		if x[2] == "0":
			num += 1
		i += 1
	db = close_conn(db)
	return render_template('view-profile.html', blocked=blocked, user=session['user'], username=username, age=Age, name=Name, surname=Surname, food=Food, music=Music, movies=Movies, animals=Animals, sports=Sports, bio=Bio, suburb=Suburb, gender=Gender, postal_code=Postal_Code, sexual_orientation=Sexual_Orientation,  noti=Noti, ImgArr=Image_Name_Arr, connectionStatus=ConnectionStatus, popularity=Popularity,num=num, NewMessage=newMessage)


@app.route('/chat/<chatUser>', methods=['GET', 'POST'])
def chat(chatUser):
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')
	db = create_conn()
	if request.method == 'POST' :
		message = request.form['message']
		sql = "INSERT INTO chats (FromUser, ToUser, Message, Read) VALUES (%s, %s, %s, %s)"
		val = (username, chatUser, message, "False")
		cursor.execute(sql, val)
		db.commit()
		sql = "UPDATE users SET NewMessage = %s WHERE username = %s"
		val = ("True", chatUser)
		cursor.execute(sql, val)
		db.commit()
	sql = "SELECT * FROM users WHERE username = %s"
	val = (session['user'], )
	cursor.execute(sql, val)
	user = cursor.fetchall()
	user = user[0]
	matches = user[3].split(', ')
	if (chatUser not in matches):
		return redirect(url_for('chats'))
	sql = "SELECT * FROM chats WHERE (FromUser = %s AND ToUser = %s) OR (FromUser = %s AND ToUser = %s))"
	values = (chatUser, username, username, chatUser)
	cursor.execute(sql, values)
	chatMessages = cursor.fetchall()
	chatMess = []
	newMessage = False
	i = 0
	while (i < len(chatMessages)):
		chatMessage = chatMessages[i]
		if chatMessage[3] == False and chatMessage[1] == username:
			newMessage = True
		if chatMessage[1] == username:
			sql = "UPDATE chats SET Read = %s WHERE ToUser = %s"
			val = ("True", username)
			cursor.execute(sql, val)
			sql = "UPDATE users SET NewMessage = %s WHERE username = %s"
			val = ("False", username)
			cursor.execute(sql, val)
		chatMess.append(chatMessage)
		i += 1
	sql = "SELECT * FROM notifications WHERE username = %s"
	val = (session['user'], )
	cursor.execute(sql, val)
	dat = cursor.fetchall()
	data = []
	num = 0
	i = 0
	while(i < len(dat)):
		x = dat[i]
		data.append(x)
		if x[2] == "0":
			num += 1
		i += 1
	db = close_conn(db)
	return render_template('chat.html', chatMessages=chatMess, chatUser=chatUser, newMessage=newMessage, user=username, num=num)

@app.route('/chats')
def chats():
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')
	db = create_conn()
	thing.noti = 'False' + username
	sql = "SELECT * FROM users WHERE username = %s"
	val = (username, )
	cursor.execute(sql, val)
	user = cursor.fetchall()
	user = user[0]
	username = session['user']
	chats = user[4]
	newMessage = user[5]
	chats = chats.split(', ')
	sql = "SELECT * FROM notifications WHERE username = %s"
	val = (session['user'], )
	cursor.execute(sql, val)
	dat = cursor.fetchall()
	data = []
	num = 0
	i = 0
	while(i < len(dat)):
		x = dat[i]
		data.append(x)
		if x[2] == "0":
			num += 1
		i += 1
	db = close_conn(db)
	return render_template('chats.html', chats=chats, newMessage=newMessage, user=username, num=num)

@app.route('/profileviews/')
def profileviews():
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')
	db = create_conn()
	thing.noti = 'False' + username
	sql = "SELECT * FROM users WHERE username = %s"
	val = (username, )
	cursor.execute(sql, val)
	user = cursor.fetchall()
	user = user[0]
	profileViews = user[17]
	newMessage = user[5]
	profileViews = profileViews.split(', ')
	sql = "SELECT * FROM notifications WHERE username = %s"
	val = (session['user'], )
	cursor.execute(sql, val)
	dat = cursor.fetchall()
	data = []
	num = 0
	i = 0
	while(i < len(dat)):
		x = dat[i]
		data.append(x)
		if x[2] == "0":
			num += 1
		i += 1
	db = close_conn(db)
	return render_template('profile-views.html', profileViews=profileViews, user=session['user'],num=num, NewMessage=newMessage)

@app.route('/profilelikes/')
def profilelikes():
	try:
		username = session['user']
	except KeyError:
		return render_template('index.html')
	if thing.hasPref == False :
		return render_template('preferences.html')
	db = create_conn()
	thing.noti = 'False' + username
	sql = "SELECT * FROM users WHERE username = %s"
	val = (username, )
	cursor.execute(sql, val)
	user = cursor.fetchall()
	user = user[0]
	profileLikes = user[18]
	profileLikes = profileLikes.split(', ')
	sql = "SELECT * FROM notifications WHERE username = %s"
	val = (session['user'], )
	cursor.execute(sql, val)
	dat = cursor.fetchall()
	data = []
	num = 0
	i =0
	while(i < len(dat)):
		x = dat[i]
		data.append(x)
		if x[2] == "0":
			num += 1
		i += 1
	db = close_conn(db)
	return render_template('profile-likes.html', profileLikes=profileLikes, user=session['user'],num=num)

@app.route('/verify/<username>', methods=['POST', 'GET'])
def verify(username):
	db = create_conn()
	sql = "SELECT * FROM users WHERE username = %s"
	val = (username, )
	cursor.execute(sql, val)
	compatibleUser = cursor.fetchall()
	compatibleUser = compatibleUser[0]
	if (compatibleUser == None or compatibleUser[2] == 1 ):
		return redirect(url_for('index'))
	mysql = "UPDATE users SET Verify = %s WHERE username = %s"
	val = ("1", username)
	cursor.execute(mysql, val)
	db.commit()
	db = close_conn(db)
	return render_template('index.html', verified=1)

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
	db = create_conn()
	if (request.method == 'GET'):
		reset = 0
		err = ''
		db = close_conn(db)
		return render_template('reset_password.html', err=err, reset=reset)
	if (request.method == 'POST'):
		reset = 0
		err = ''
		email = request.form['email']
		if (len(email) > 0):
			emailCheck = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
			if (re.search(emailCheck, email)):
				sql = "SELECT * FROM users WHERE Email = %s"
				val = (email)
				cursor.execute(sql, val)
				result = cursor.fetchall()
				result = result[0]
				if (result == None):
					err = 3
					db = close_conn(db)
					return render_template('reset_password.html', err=err, reset=reset)
				else:
					err = 0
					token = hash_password(email)
					sql = "UPDATE users SET Token = %s WHERE Email = %s"
					val = (token, email)
					cursor.execute(sql, val)
					db.commit()
					msg = Message("Matcha Password Reset", sender="noreply@matcha.com", recipients=[email])
					msg.body = "Hello!\n\nYou have requested a password reset. Please click the link below to verify your account and reset your password.\n\nhttp://127.0.0.1:5000/reset?email={0}&token={1}.\n\nThank you.\n".format(email, token)
					mail.send(msg)
					db = close_conn(db)
					return render_template('reset_password.html', err=err, reset=reset)
			elif not (re.search(emailCheck, email)):
				err = 1
				db = close_conn(db)
				return render_template('reset_password.html', err=err, reset=reset)
		else :
			err = 2
			db = close_conn(db)
			return render_template('reset_password.html', err=err, reset=reset)

@app.route('/reset', methods=['GET', 'POST'])
def reset():
	db = create_conn()
	if (request.method == 'GET'):
		err = ''
		reset = 1
		email = request.args.get('email')
		token = request.args.get('token')
		cursor.execute("SELECT * FROM users WHERE Email = %s")
		validEmail = cursor.fetchall()
		validEmail = validEmail[0]
		cursor.execute("SELECT * FROM users WHERE Token = %s")
		validToken = cursor.fetchall()
		validToken = validToken[0]
		if (validEmail == None or validToken == None):
			err = 4
			db = close_conn(db)
			return render_template('reset_password.html', err=err, reset=reset)
		else:
			err = 5
			db = close_conn(db)
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
				sql = "UPDATE users SET Token = %s, Password = %s WHERE Email = %s"
				val = ("", hash_password(password), email)
				cursor.execute(sql, val)
				db.commit()
				db = close_conn(db)
				return redirect(url_for('index'))
			else:
				err = 7
				db = close_conn(db)
				return render_template('index.html', err=err, reset=reset)
		else:
			err = 8
			db = close_conn(db)
			return render_template('index.html', err=err, reset=reset)
		db = close_conn(db)
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