import os, requests
from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from werkzeug.contrib.fixers import ProxyFix
from flask import Flask, redirect, url_for
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook
from raven.contrib.flask import Sentry
from requests_toolbelt.adapters import appengine

# Init App
appengine.monkeypatch()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.wsgi_app = ProxyFix(app.wsgi_app)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = os.environ.get("OAUTHLIB_INSECURE_TRANSPORT")
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = os.environ.get("OAUTHLIB_RELAX_TOKEN_SCOPE")

# Config Google OAuth

app.config["GOOGLE_OAUTH_CLIENT_ID"] = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
google_bp = make_google_blueprint(scope=['https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'])
app.register_blueprint(google_bp, url_prefix="/login")

# Config Facebook OAuth
app.config["FACEBOOK_OAUTH_CLIENT_ID"] = os.environ.get("FACEBOOK_OAUTH_CLIENT_ID")
app.config["FACEBOOK_OAUTH_CLIENT_SECRET"] = os.environ.get("FACEBOOK_OAUTH_CLIENT_SECRET")
facebook_bp = make_facebook_blueprint(scope=['email'],rerequest_declined_permissions=True)
app.register_blueprint(facebook_bp, url_prefix="/login")

# Config MySQL
app.config['MYSQL_HOST'] = os.environ.get("MYSQL_HOST")
app.config['MYSQL_UNIX_SOCKET'] = os.environ.get("MYSQL_UNIX_SOCKET")
app.config['MYSQL_USER'] = os.environ.get("MYSQL_USER")
app.config['MYSQL_PASSWORD'] = os.environ.get("MYSQL_PASSWORD")
app.config['MYSQL_DB'] = os.environ.get("MYSQL_DB")
app.config['MYSQL_CURSORCLASS'] = os.environ.get("MYSQL_CURSORCLASS")

mysql = MySQL(app)

# Google Recaptcha
def check_recaptcha(f):
    """
    Checks Google  reCAPTCHA.

    :param f: view function
    :return: Function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request.recaptcha_is_valid = None

        if request.method == 'POST':
            data = {
                'secret': os.environ.get('RECAPTCHA_SECRET_KEY'),
                'response': request.form.get('g-recaptcha-response'),
                'remoteip': request.access_route[0]
            }
            r = requests.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data=data
            )
            result = r.json()

            if result['success']:
                request.recaptcha_is_valid = True
                # flash('Valid reCAPTCHA', 'success')
            else:
                request.recaptcha_is_valid = False
                flash('Invalid reCAPTCHA. Please try again.', 'danger')

        return f(*args, **kwargs)

    return decorated_function

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
    # Create Cursor
    cur = mysql.connection.cursor()
    # Get Articles
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = "No articles found"
        return render_template('articles.html', msg=msg)
    # Close Connections
    cur.close() 
    # return render_template('dashboard.html')

# Single Article
@app.route('/article/<string:id>/')
def article(id):
    # Create Cursor
    cur = mysql.connection.cursor()
    # Get Articles  ?? RESULT ??
    result = cur.execute("SELECT * FROM articles WHERE id=%s",[id])
    article = cur.fetchone()
    return render_template('article.html', article=article)

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
@check_recaptcha
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate() and request.recaptcha_is_valid:
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
    return render_template('register.html', form=form, RECAPTCHA_SITE_KEY = os.environ.get("RECAPTCHA_SITE_KEY"))
    
# User Login
@app.route('/login', methods=['GET', 'POST'])
@check_recaptcha
def login():
    if request.method == 'POST' and request.recaptcha_is_valid:
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
    return render_template('login.html', RECAPTCHA_SITE_KEY = os.environ.get("RECAPTCHA_SITE_KEY"))

# User Login Google
@app.route('/login_google', methods=['GET', 'POST'])
def login_google():
    if not google.authorized:
        return redirect(url_for("google.login"))
    resp = google.get("/oauth2/v1/userinfo")
    if resp.ok and resp.text:
        name = resp.json()["name"]
        email = resp.json()["email"]
        username = resp.json()["given_name"]
        oauth_id = resp.json()["id"]
        print resp.json()
        
        # Create cursor
        cur = mysql.connection.cursor()
        # Get user by email
        result = cur.execute("SELECT * FROM users WHERE email =%s AND oauth_id =%s", [email,oauth_id])
        if result>0:
            # data = cur.fetchone()
            session['logged_in'] = True
            session['username'] = username
            # Close connection
            cur.close()
            flash('You are now logged in via Google','success')
            return redirect(url_for('dashboard'))
        else:
            # Execute Query
            cur.execute("INSERT INTO users(name, email, username, oauth_id) VALUES(%s, %s, %s, %s)", (name, email, username, oauth_id))
            # Commit to DB
            mysql.connection.commit()
            # Close connection
            cur.close()

            session['logged_in'] = True
            session['username'] = username
            flash('Successfully registered via Google','success')
            return redirect(url_for('dashboard'))

# User Login Facebook
@app.route('/login_facebook', methods=['GET', 'POST'])
def login_facebook():
    if not facebook.authorized:
        return redirect(url_for("facebook.login"))
    resp = facebook.get("me?fields=id,name,email,first_name,short_name")
    if resp.ok:
        name = resp.json()["name"]
        email = resp.json()["email"]
        username = resp.json()["short_name"]
        oauth_id = resp.json()["id"]
        
        # Create cursor
        cur = mysql.connection.cursor()
        # Get user by email
        result = cur.execute("SELECT * FROM users WHERE email =%s AND oauth_id=%s", [email,oauth_id])
        if result>0:
            print "THIS WORKSSSSSSSSSSSSSSSS"
            # data = cur.fetchone()
            session['logged_in'] = True
            session['username'] = username
            # Close connection
            cur.close()
            flash('You are now logged in via Facebook','success')
            return redirect(url_for('dashboard'))
        else:
            # Execute Query
            cur.execute("INSERT INTO users(name, email, username, oauth_id) VALUES(%s, %s, %s, %s)", (name, email, username, oauth_id))
            # Commit to DB
            mysql.connection.commit()
            # Close connection
            cur.close()

            session['logged_in'] = True
            session['username'] = username
            flash('Successfully registered via Facebook','success')
            return redirect(url_for('dashboard'))

# Check if user logged in
def is_user_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
# @is_user_logged_in
def logout():
    session.clear()
    flash('You are now logged out','success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_user_logged_in
def dashboard():
    # Create Cursor
    cur = mysql.connection.cursor()

    # Get Articles
    result = cur.execute("SELECT * FROM articles WHERE author = %s", [session['username']])
    # result = cur.execute("SELECT * FROM articles")
    
    articles = cur.fetchall()

    # Close Connections
    cur.close()
    
    if result>0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = "No articles found"
        return render_template('dashboard.html', msg=msg)
    
# Article Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=280)])
    body = TextAreaField('Body', [validators.Length(min=30)])

# Add Article
@app.route('/add_article', methods=['GET','POST'])
@is_user_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute Query
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('Article Created', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form)

# Edit Article
@app.route('/edit_article/<string:id>/', methods=['GET', 'POST'])
@is_user_logged_in
def edit_article(id):
    # Create Cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM articles WHERE id=%s",[id])

    article = cur.fetchone()

    # Get form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute Query
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s", (title,body,id))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('Article Updated', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_article.html', form=form)

# Delete Article
@app.route('/delete_article/<string:id>/', methods=['POST'])
@is_user_logged_in
def delete_article(id):
    # Create Cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM articles WHERE id=%s", [id])

    # Commit to DB
    mysql.connection.commit()

    # Close connection
    cur.close()

    flash('Article Deleted', 'success')
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)
