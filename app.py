from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'assassin47'
app.config['MYSQL_DB'] = 'myFlaskApp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Initialize MySQL
mysql = MySQL(app)

Articles = Articles()

# Index
@app.route('/')
def index():
	return render_template('home.html')

# About
@app.route('/about')
def about():
	return render_template('about.html')

# Articles
@app.route('/articles')
def articles():
	return render_template('articles.html', articles = Articles)

# Single Article
@app.route('/article/<string:id>/')
def article(id):
	return render_template('article.html', id=id)

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404

# Register Form Class
class RegisterForm(Form):
	name = StringField('Name', [validators.Length(min=1,max=50)])
	username = StringField('Username', [validators.Length(min=4,max=25)])
	email = StringField('Email', [validators.Length(min=6,max=50)])
	password = PasswordField('Password', [
		validators.DataRequired(), 
		validators.EqualTo('confirm', message='Passwords do not match')
	])
	confirm = PasswordField('Confirm Password')

# User Register
@app.route('/register', methods=['GET','POST'])
def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		email = form.email.data
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data))
		# Create cursor
		cur = mysql.connection.cursor()
		# Execute Query
		cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))
		# Commit to DB
		mysql.connection.commit()
		# Close connection
		cur.close()

		flash('You are registered and can log in', 'Success!')
		return redirect(url_for('index'))
	return render_template('register.html', form=form)
	
# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		# Get Form Fields
		username = request.form['username']
		password_candidate = request.form['password']

		# Create cursor
		cur = mysql.connection.cursor()

		# Get user by username
		result = cur.execute("SELECT * FROM users WHERE username =%s", [username])
		
		if result > 0:
			# Get stored hash
			data = cur.fetchone()
			password = data['password']

			# Compare Passwords
			if sha256_crypt.verify(password_candidate, password):
				session['logged_in'] = True
				session['username'] = username
				flash('You are now logged in','success')
				return redirect(url_for('dashboard'))
			else:
				error = 'Invalid Password'
				return render_template('login.html', error=error)
			
			# Close Connection
			cur.close()
		else:
			error = 'Username is not found'
			return render_template('login.html', error=error)

	return render_template('login.html')


# Logout
@app.route('/logout')
def logout():
	session.clear()
	flash('You are now logged out','success')
	return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
def dashboard():
	return render_template('dashboard.html')

if __name__ == '__main__':
	app.secret_key='secret123'
	app.run(debug=True)
