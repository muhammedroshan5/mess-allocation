import sqlite3
from flask import Flask, render_template, request, url_for, flash, redirect, session, abort, make_response
from werkzeug.exceptions import abort
from flask_mail import Mail, Message
import mail_config
import random, string, secrets
import requests
import openpyxl



def download():
    # create a new workbook
    wb = openpyxl.Workbook()
    
    # get the active worksheet
    ws = wb.active
    
    # create some sample data
    data = [
        ['Name', 'Age', 'Email'],
        ['John Doe', 25, 'john.doe@example.com'],
        ['Jane Smith', 30, 'jane.smith@example.com'],
        ['Bob Johnson', 40, 'bob.johnson@example.com'],
    ]
    
    # write the data to the worksheet
    for row in data:
        ws.append(row)
    
    # create a response object
    response = make_response(wb.save('data.xlsx'))
    
    # set the headers to trigger a file download
    response.headers['Content-Disposition'] = 'attachment; filename=data.xlsx'
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    return response	

def connect_db():
	conn=sqlite3.connect('database.db')
	conn.row_factory=sqlite3.Row
	
	return conn
	
def get_post_student(username):
	conn=connect_db()
	post=conn.execute('SELECT * FROM student where username = ?',(username,)).fetchone()
	conn.close()
	if post is None:
		abort(404)
		
	return post

def get_post_admin(username):
	conn=connect_db()
	post=conn.execute('SELECT * FROM admin where username = ?',(username,)).fetchone()
	conn.close()
	
	if post is None:
		abort(404)
		
	return post

def get_mess_admin(name):
	conn=connect_db()
	post=conn.execute('SELECT * FROM mess where name = ?',(name,)).fetchone()
	conn.close()
	
	if post is None:
		abort(404)
	print(post)
	return post


def get_mess_check(messname,username):

	conn=connect_db()
	
	mess=conn.execute('SELECT COUNT(*) FROM student where mess = ?',(messname,)).fetchone()
	current_count = mess[0]
	mess=conn.execute('SELECT * FROM mess where name = ?',(messname,)).fetchone()
	max_capacity = mess['capacity']
	
	if current_count < max_capacity:
		print(current_count,max_capacity)
		conn.execute("UPDATE student SET mess = ? WHERE username = ?",(messname,username))
		conn.commit()
		conn.close()
		return True
	else:
		conn.commit()
		conn.close()
		return False
		
def get_mess(username):

	conn=connect_db()
	user=conn.execute('SELECT * FROM student where username = ?',(username,)).fetchone()
	gender=user['gender']
	mess = list()
	
	if gender=='Female':
		mess_choice = conn.execute("SELECT * FROM mess WHERE category = 'G' OR category = 'M'").fetchall()
		for choice in mess_choice:
			mess.append(choice['name'])
	else:
		mess_choice = conn.execute("SELECT * FROM mess WHERE category = 'B' OR category = 'M'").fetchall()
		for choice in mess_choice:
			mess.append(choice['name'])
	
	return mess

def get_student_from_mess(messname):
	conn=connect_db()
	post=conn.execute('SELECT * FROM student where mess = ?',(messname,)).fetchall()
	conn.close()
	
	if post is None:
		abort(404)
		
	return post
	
def get_student_details():
	conn=connect_db()
	post=conn.execute('SELECT * FROM student').fetchall()
	conn.close()
	
	if post is None:
		abort(404)
	return post
	
def get_student(studname):
	conn=connect_db()
	post=conn.execute('SELECT * FROM student WHERE name = ?',(studname,)).fetchone()
	conn.close()
	if post is None:
		abort(404)
	return post

app = Flask(__name__)
#app = Flask("__name__")
app.config['SECRET_KEY'] = 'your key bleh'


mail = Mail(app) # instantiate the mail class
   
# configuration of mail
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = mail_config.sender_mail()
app.config['MAIL_PASSWORD'] = mail_config.pass_word()
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)



@app.route('/',methods=('GET', 'POST'))
def index():
	session['username'] = ";;;"
	if request.method == 'POST':
	
		username = request.form['username']
		pwd = request.form['pwd']
		adorstu = request.form.get('utype')
		
		if adorstu == "student":
			conn = connect_db()
			user = conn.execute("SELECT id FROM student WHERE username = ? AND pwd = ?",(username,pwd)).fetchall()
			if user == []:
				flash("Username&Password not found!!!")
			else:
				user = get_post_student(username)
				session['username'] = username
				if user['hostel'] is None:
					return redirect(url_for('create_profile',username=username))
				else:
					return redirect(url_for('show_profile',username=username))
		else:
			conn = connect_db()
			user = conn.execute("SELECT id FROM admin WHERE username = ? AND pwd = ?",(username,pwd)).fetchall()
			if user == []:
				flash("Username&Password not found!!!")
			else:
				session['username'] = username
				return redirect(url_for('admin',username=username))
				
	return render_template('index.html')
	
@app.route('/<username>/create_profile',methods=('GET','POST'))
def create_profile(username):

	if username != session['username']:
		abort(401)

	if request.method == 'POST':
	
		if request.form['action'] == 'save':
			gender = request.form.get('gender')
			hostel = request.form['hostel']
			room = request.form['room']
			
			if gender == "default" or hostel == "None" or room == "None":
				flash("Fill the options and Click Save Changes to Continue")
			else:	
				conn = connect_db()
				conn.execute("UPDATE student SET gender = ?, hostel = ?, room = ? WHERE username = ?",(gender,hostel,room,username))
				conn.commit()
				conn.close()
				return redirect(url_for('show_profile',username=username))		
		elif request.form['action'] == 'payment':
			return redirect("https://www.onlinesbi.sbi/sbicollect/icollecthome.htm")

	user = get_post_student(username)
	email=user['email']
	
	return render_template('profile_student.html',user=user,email=email,username=username)
	
	
@app.route('/<username>/profile',methods=('GET','POST'))
def show_profile(username):

	if username != session['username']:
		abort(401)

	user = get_post_student(username)

	if user['mess'] is None:
		flag=True
	else:
		flag=False
		
	name=user['name']
	fname=name.split()
	email=fname[0].lower()+'_'+username.lower()+'@nitc.ac.in'	

	if request.method == 'POST':
	
		if request.form['action'] == 'continue':
			if user['due']>0:
				flash("Clear Mess dues!")
				return render_template('show_profile.html',user=user,email=email,flag=flag,username=username)
			return redirect(url_for('mess_preference',username=username))
		elif request.form['action'] == 'edit':
			return redirect(url_for('create_profile',username=username))
		elif request.form['action'] == 'change':
			return redirect(url_for('change_password',username=username))
		elif request.form['action'] == 'payment':
			return redirect("https://www.onlinesbi.sbi/sbicollect/icollecthome.htm")	
	
		
		
	return render_template('show_profile.html',user=user,email=email,flag=flag,username=username)

@app.route('/<username>/profile/change_password',methods=('GET','POST'))
def change_password(username):

	if username != session['username']:
		abort(401)

	user = get_post_student(username)

	if request.method == 'POST':
		if request.form['action'] == 'change':
			old = request.form['old']
			new = request.form['new']
			confirm = request.form['confirm']

			if user['pwd'] != old:
				flash("Old password does not match")
				return render_template('change_password.html',user=user,username=username)
			elif new != confirm:
				flash("New password & Confirm password does not match!")
			elif old == new:
				flash("Your old password and new password cannot be same")
			else:
				conn = connect_db()
				conn.execute("UPDATE student SET pwd = ? where username = ?",(new,username))
				conn.commit()
				conn.close()
				return redirect(url_for('show_profile',username=username))

		elif request.form['action'] == 'goback':
			return redirect(url_for('show_profile',username= username))
	return render_template('change_password.html',user=user,username=username)
	
	
@app.route('/<username>/profile/mess_preference',methods=('GET','POST'))
def mess_preference(username):

	if username != session['username']:
		abort(401)

	user = get_post_student(username)
	mess = get_mess(username)
	
	if request.method == 'POST':
		if request.form['action'] == 'submit':
			choices = list()
			choices.append(request.form.get('mess1'))
			choices.append(request.form.get('mess2'))
			choices.append(request.form.get('mess3'))
			choices.append(request.form.get('mess4'))
			choice_final = [value for value in choices if value != " "]
			
			if (len(choice_final) != len(set(choice_final))):
				flash("Select different mess for each preference!!!")
			else:
				flag=0
				for choice in choice_final:
					if get_mess_check(choice,username) == True:
						flag=1
						break
						
				return render_template('mess_final.html',flag=flag,username=username)
		if request.form['action'] == 'goback':
			return redirect(url_for('show_profile',username=username))
		
	return render_template('mess_preference.html',mess=mess,username=username)

@app.route('/<username>/admin',methods=('GET','POST'))
def admin(username):

	if username != session['username']:
		abort(401)

	user = get_post_admin(username)
	if request.method == 'POST':
		if request.form['action'] == 'mess':
			return redirect(url_for('admin_mess',username=username))
		if request.form['action'] == 'student':
			return redirect(url_for('admin_student',username=username))
		
	return render_template('admin.html',user=user,username=username)

@app.route('/<username>/admin/admin_mess',methods=('GET','POST'))
def admin_mess(username):

	if username != session['username']:
		abort(401)

	user = get_post_admin(username)
	conn=connect_db()
	mess=conn.execute('SELECT * FROM mess').fetchall()
	conn.close()
	if request.method == 'POST':
		if request.form['action'] == 'goback':
			return redirect(url_for('admin',username=username))
		if request.form['action'] == 'addmess':
			return redirect(url_for('admin_addmess',username=username))
		if request.form['action'] == 'clearmess':
			conn=connect_db()
			conn.execute("UPDATE student SET mess = NULL")
			conn.commit()
			conn.close()
		else:
			messname = request.form['action']
			return redirect(url_for('admin_mess_details',messname=messname,username=username))
			
	return render_template('admin_mess.html',user=user, mess=mess, username=username)

@app.route('/<username>/admin/admin_mess/<messname>/admin_mess_details',methods=('GET','POST'))
def admin_mess_details(messname,username):

	if username != session['username']:
		abort(401)

	mess=get_mess_admin(messname)	
	student=get_student_from_mess(messname)
	if request.method == 'POST':
		if request.form['action'] == 'goback':
			return redirect(url_for('admin_mess', username=username))
		if request.form['action'] == 'updatemess':
			return redirect(url_for('admin_updatemess', messname=messname, username=username))
	return render_template('admin_mess_details.html',mess=mess,student=student,username=username)

@app.route('/<username>/admin/admin_mess/<messname>/admin_mess_details/admin_updatemess',methods=('GET','POST'))
def admin_updatemess(messname,username):

	if username != session['username']:
		abort(401)

	mess=get_mess_admin(messname)
	if request.method == 'POST':
		if request.form['action'] == 'goback':
			return redirect(url_for('admin_mess_details', messname=messname, username=username))
		if request.form['action'] == 'save':
			name = messname
			capacity = request.form['capacity']
			category = request.form.get('category')
			owner = request.form['owner']
			
			if category == "default" or name == "None" or owner == "None" or capacity == "None":
				flash("Fill the options and Click Save to Continue")
			else:	
				conn = connect_db()
				conn.execute("UPDATE mess SET name = ?, capacity = ?, category = ?, owner = ? WHERE name = ?",(name,capacity,category,owner,messname))
				conn.commit()
				conn.close()
				return redirect(url_for('admin_mess_details', messname=name, username=username))
	return render_template('admin_updatemess.html', mess=mess,username=username)
	
@app.route('/<username>/admin/admin_mess/admin_addmess',methods=('GET','POST'))
def admin_addmess(username):

	if username != session['username']:
		abort(401)

	if request.method == 'POST':
		if request.form['action'] == 'goback':
			return redirect(url_for('admin_mess',username=username))
		if request.form['action'] == 'add':
			name = request.form.get('name')
			capacity = request.form['capacity']
			owner = request.form['owner']
			category = request.form.get('category')
			
			if name == "None" or capacity == "None" or owner == "None" or category == "default":
				flash("Fill the options and Click Add")
			else:	
				conn = connect_db()
				conn.execute("INSERT INTO mess(name,capacity,owner,category) VALUES(?,?,?,?);",(name,capacity,owner,category))
				conn.commit()
				conn.close()
				return redirect(url_for('admin_mess',username=username))
	return render_template('admin_addmess.html',username=username)
	

	
	
@app.route('/<username>/admin/admin_student',methods=('GET','POST'))
def admin_student(username):

	if username != session['username']:
		abort(401)

	user = get_post_admin(username)
	student=get_student_details()
	student_list = list()
	
	for students in student:
		student_list.append(students['username'])
	
	if request.method == 'POST' and 'action' in request.form:
		if request.form['action'] == 'add':
			return redirect(url_for('add_student',username=username))
		elif request.form['action'] == 'search':
			stud = request.form['username']
			conn=connect_db()
			student = conn.execute("SELECT * FROM student where username = ? or name = ?",(stud,stud)).fetchall()
	elif request.method == 'POST':
		# download()
		pass

	return render_template('admin_student.html',student=student,user=user,student_list=student_list,username=username)
	
	
@app.route('/<username>/admin/admin_student/add_student',methods=('GET','POST'))
def add_student(username):

	if username != session['username']:
		abort(401)

	if request.method == 'POST':
		if request.form['action'] == 'goback':
			return redirect(url_for('admin_student',username=username))
		if request.form['action'] == 'add':
			name = request.form['name']
			roll = request.form['roll']
			if name=="" or roll=="":
				flash("Fill the options and Click Add")
			else:
				conn = connect_db()
				conn.execute("INSERT INTO student (name, username, pwd) VALUES (?, ?, ?);",(name, roll, roll))
				conn.commit()
				conn.close()
				return redirect(url_for('admin_student',username=username))
	return render_template('add_student.html',username=username)	
	
	
@app.route('/<username>/admin/admin_student/<studname>/edit_student',methods=('GET','POST'))
def edit_student(username,studname):

	if username != session['username']:
		abort(401)

	student=get_student(studname)
	id = student['id']
	if request.method == 'POST':
		if request.form['action'] == 'goback':
			return redirect(url_for('admin_student',username=username))
		if request.form['action'] == 'save':
			name = student['name']
			roll = student['username']
			due = request.form['due']
			conn = connect_db()
			conn.execute("UPDATE student SET name = ?, username = ?, pwd = ?, due = ? WHERE id = ?",(name, roll, roll, due, id))
			conn.commit()
			conn.close()
			return redirect(url_for('admin_student',username=username))
	return render_template('edit_student.html',username=username,student=student)	
	
	
@app.route('/forgot_password',methods=('GET','POST'))
def forgot_password():

	if request.method == 'POST':
		if request.form['action'] == 'forgot':
			mailid = request.form['usermail']
			if mailid == "":
				flash("Enter your mail-id!")
				return render_template('forgot_password.html')
			index = mailid.index('@')
			if mailid[index+1:] != 'nitc.ac.in':
				flash("This is not a valid Institute mail id!")
				return render_template('forgot_password.html')
			else:
				res = ''.join(secrets.choice(string.ascii_letters + string.digits) for x in range(6))  #password generator
				index = mailid.index('_')
				username = mailid[index+1:index+10].upper()
				msg = Message('Password Reset', sender = mail_config.sender_mail(), recipients = [mailid])
				msg.body = """This is a no-reply mail.
				
				
Your login-credentials for mess allocation are:

Username : {}
Password : {}""".format(username.upper(),str(res))
				mail.send(msg)
				
			conn = connect_db()
			user = conn.execute("SELECT id FROM student WHERE username = ?",(username,)).fetchall()
			if user != []:
				conn.execute("UPDATE student SET pwd = ? WHERE username = ?",(str(res),username))
				conn.commit()
				conn.close()
				
			return render_template('mail_sent.html')


		elif request.form['action'] == 'goback':
			return redirect(url_for('index'))
	
	return render_template('forgot_password.html')

@app.route('/logout',methods=('GET','POST'))
def logout():
	session['username'] = ";;;"
	return redirect(url_for('index'))
	

@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    return response

	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
