import os
import requests

from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from werkzeug.contrib.fixers import ProxyFix
from flask import Flask, redirect, url_for
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook
from raven.contrib.flask import Sentry
from requests_toolbelt.adapters import appengine

import datetime
import os
from google.appengine.ext import ndb

# Init App
appengine.monkeypatch()
app = Flask(__name__)

# os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="credentials.json"
app.config["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"

app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.wsgi_app = ProxyFix(app.wsgi_app)
app.config['OAUTHLIB_INSECURE_TRANSPORT'] = os.environ.get(
    "OAUTHLIB_INSECURE_TRANSPORT")
app.config['OAUTHLIB_RELAX_TOKEN_SCOPE'] = os.environ.get(
    "OAUTHLIB_RELAX_TOKEN_SCOPE")

# Config Google OAuth
app.config["GOOGLE_OAUTH_CLIENT_ID"] = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = os.environ.get(
    "GOOGLE_OAUTH_CLIENT_SECRET")
google_bp = make_google_blueprint(
    scope=['https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'])
app.register_blueprint(google_bp, url_prefix="/login")

# Config Facebook OAuth
app.config["FACEBOOK_OAUTH_CLIENT_ID"] = os.environ.get(
    "FACEBOOK_OAUTH_CLIENT_ID")
app.config["FACEBOOK_OAUTH_CLIENT_SECRET"] = os.environ.get(
    "FACEBOOK_OAUTH_CLIENT_SECRET")
facebook_bp = make_facebook_blueprint(
    scope=['email'], rerequest_declined_permissions=True)
app.register_blueprint(facebook_bp, url_prefix="/login")

# init Datastore
# ds = datastore.Client()

# Google Recaptcha
def check_recaptcha(f):
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
                flash('Valid reCAPTCHA', 'success')
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
    query1 = Article.query().order(Article.id)
    query3 = query1.fetch()

    articles = []
    for entity in query3:
        article = {}
        article['id'] = entity.id
        article['title'] = entity.title
        articles.append(article)

    if len(query3) > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = "No articles found"
        return render_template('articles.html', msg=msg)

# Single Article
@app.route('/article/<string:id>/')
def article(id):
    query1 = Article.query()
    query2 = query1.filter(Article.id == int(id))
    query3 = query2.fetch()

    return render_template('article.html', article=query3[0])


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

# Add User Model
class AddUser(ndb.Model):
    name = ndb.StringProperty()
    email = ndb.StringProperty()
    username = ndb.StringProperty()
    password = ndb.StringProperty()
    oauth_id = ndb.StringProperty()
    register_date = ndb.DateTimeProperty(auto_now_add=True)

# User Register
@app.route('/register', methods=['GET', 'POST'])
@check_recaptcha
def register():
    form = RegisterForm(request.form)

    if request.method == 'POST' and form.validate() and request.recaptcha_is_valid:
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        addUser = AddUser()
        addUser.name = name
        addUser.email = email
        addUser.username = username
        addUser.password = password
        addUser.put()

        flash('You are registered and can log in', 'Success!')
        return redirect(url_for('index'))

    return render_template('register.html', form=form, RECAPTCHA_SITE_KEY=os.environ.get("RECAPTCHA_SITE_KEY"))

# User Login
@app.route('/login', methods=['GET', 'POST'])
@check_recaptcha
def login():
    if request.method == 'POST' and request.recaptcha_is_valid:

        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        query1 = AddUser.query()
        query2 = query1.filter(AddUser.username == username)
        query3 = query2.fetch()

        if len(query3) > 0:
            password = query3[0].password

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username
                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid Password'
                return render_template('login.html', error=error)

        else:
            error = 'Username is not found'
            return render_template('login.html', error=error)

    return render_template('login.html', RECAPTCHA_SITE_KEY=os.environ.get("RECAPTCHA_SITE_KEY"))

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

        query1 = AddUser.query()
        query2 = query1.filter(AddUser.username == username)
        query3 = query2.fetch()

        if len(query3) > 0:
            session['logged_in'] = True
            session['username'] = username

            flash('You are now logged in via Google', 'success')
            return redirect(url_for('dashboard'))
        else:

            addUser = AddUser()
            addUser.name = name
            addUser.email = email
            addUser.username = username
            addUser.oauth_id = oauth_id
            addUser.put()

            session['logged_in'] = True
            session['username'] = username
            flash('Successfully registered via Google', 'success')
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

        query1 = AddUser.query()
        query2 = query1.filter(AddUser.username == username)
        query3 = query2.fetch()

        if len(query3) > 0:
            session['logged_in'] = True
            session['username'] = username

            flash('You are now logged in via Facebook', 'success')
            return redirect(url_for('dashboard'))
        else:

            addUser = AddUser()
            addUser.name = name
            addUser.email = email
            addUser.username = username
            addUser.oauth_id = oauth_id
            addUser.put()

            session['logged_in'] = True
            session['username'] = username
            flash('Successfully registered via Facebook', 'success')
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
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_user_logged_in
def dashboard():

    query3 = []
    query1 = Article.query().order(Article.id)
    query2 = query1.filter(Article.author == session['username'])
    query3 = query2.fetch()

    if len(query3) > 0:
        return render_template('dashboard.html', articles=query3)
        # return render_template('dashboard.html', articles=articles)
    else:
        msg = "No articles found"
        return render_template('dashboard.html', msg=msg)

# Article Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=280)])
    body = TextAreaField('Body', [validators.Length(min=30)])

class ArticleCounterModel(ndb.Model):
    count = ndb.IntegerProperty(default=1)

class Article(ndb.Model):
    id = ndb.IntegerProperty()
    title = ndb.StringProperty()
    body = ndb.StringProperty()
    author = ndb.StringProperty()
    create_date = ndb.DateTimeProperty(auto_now_add=True)

# Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_user_logged_in
def add_article():
    form = ArticleForm(request.form)
    key_id = ArticleCounterModel.query().fetch()

    if key_id == []:
        newCounter = ArticleCounterModel()
        newCounter.put()
        key_id = ArticleCounterModel.query().fetch()

    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        addArticle = Article()
        addArticle.id = key_id[0].count
        addArticle.title = title
        addArticle.body = body
        addArticle.author = session['username']
        addArticle.put()

        key_id[0].count += 1
        key_id[0].put()

        flash('Article Created', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)

# Edit Article
@app.route('/edit_article/<string:id>/', methods=['GET', 'POST'])
@is_user_logged_in
def edit_article(id):
    # Get form
    form = ArticleForm(request.form)

    query1 = Article.query()
    query2 = query1.filter(Article.author == session['username'])
    query3 = query1.filter(Article.id == int(id))
    query4 = query3.fetch()

    # Populate article form fields
    form.title.data = query4[0].title
    form.body.data = query4[0].body

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        query4[0].title = request.form['title']
        query4[0].body = request.form['body']
        query4[0].put()

        flash('Article Updated', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

# Delete Article
@app.route('/delete_article/<string:id>/', methods=['POST'])
@is_user_logged_in
def delete_article(id):

    query1 = Article.query()
    query2 = query1.filter(Article.author == session['username'])
    query3 = query1.filter(Article.id == int(id))
    query4 = query3.fetch()
    print query4[0].id == int(id)
    query4[0].key.delete()

    # key_id = ArticleCounterModel.query().fetch()
    # key_id[0].count -= 1
    # key_id[0].put()

    flash('Article Deleted', 'success')
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)
