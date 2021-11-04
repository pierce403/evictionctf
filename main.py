import flask
from flask import render_template
from flask import request
from flask import Flask
from flask import g

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# scrypt 14 for password hashing
from flask_scrypt import generate_password_hash, generate_random_salt, check_password_hash

import random
import string

app = Flask(__name__,static_url_path='/static')
# ~120 bits of entropy
#app.secret_key = 'potato'
app.secret_key = ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(20))
print("key is "+app.secret_key)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eviction.db'
db = SQLAlchemy(app)

from flask_login import LoginManager, login_user, login_required, logout_user, current_user
login_manager = LoginManager()
login_manager.init_app(app)

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import Email, DataRequired
class SignupForm(FlaskForm):
    # TODO add some validators for user/pass
    username = StringField('username',validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    submit = SubmitField("Sign In")

#from login import *
class User(db.Model):
    username = db.Column(db.String(80), primary_key=True, unique=True)
    password_hash = db.Column(db.String(80))
    salt = db.Column(db.String(80))
    ioc = db.Column(db.String(80))

    red_points = db.Column(db.Integer)
    blue_points = db.Column(db.Integer)
    heat = db.Column(db.Integer) # number of tags in a row

    ctime = db.Column(db.DateTime(),default=datetime.now)
    mtime = db.Column(db.DateTime(),onupdate=datetime.now)

    def burn(self):
      self.ioc = ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(10))

    def __init__(self, username, password):
        self.username = username
        self.salt = generate_random_salt()
        self.password_hash = generate_password_hash(password, self.salt)

        self.red_points=0
        self.blue_points=0
        self.heat=0

        self.burn()
    def __repr__(self):
        return '<User %r>' % self.username

    def is_authenticated(self):
        return True
    def is_active(self):
        return True
    def is_anonymous(self):
        return False
    def get_id(self):
        return str(self.username)

class IOCs(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  ioc = db.Column(db.String(80))
  active = db.Column(db.Boolean)
  creator = db.Column(db.String(80))
  destroyer = db.Column(db.String(80))
  ctime = db.Column(db.DateTime,default=datetime.utcnow)

class Signals(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user = db.Column(db.String(80))
  ioc = db.Column(db.String(80))
  points = db.Column(db.Float)
  ctime = db.Column(db.DateTime,default=datetime.utcnow)

db.create_all()

@app.route('/')
def home():

  form = SignupForm()

  if not current_user.is_authenticated:
    return render_template("login.html",form=form)

  # get scores
  top_red = User.query.order_by(-User.red_points).limit(5).all()
  top_blue = User.query.order_by(-User.blue_points).limit(5).all()

  return render_template("index.html",current_user=current_user,top_blue=top_blue,top_red=top_red)

@app.route('/tag')
def flag():
  ioc = request.args.get('ioc')
  if not ioc:
    return "no IOC specified"

  target_user = User.query.filter_by(ioc=ioc).first()
  if not target_user:
    return "invalid IOC"

  try:
    delay = datetime.now().timestamp()-target_user.mtime.timestamp()
    if delay < 600:
      return "must wait 10 minutes between taggings ("+str(600-int(delay))+" seconds remaining)"
  except:
    print("that was fun")

  if target_user.heat<10:
    target_user.heat = int(target_user.heat)+1
  target_user.red_points = int(target_user.red_points) + target_user.heat
  db.session.commit()

  return "yay"


@app.route('/scoreboard')
def signals():

  users = User.query.all()

  return render_template("score.html",users=users)

@app.route('/burn', methods=['POST'])
@login_required
def burn():
  ioc = request.form.get('ioc')
  if not ioc:
    return "no IOC specified"

  target_user = User.query.filter_by(ioc=ioc).first()
  if not target_user:
    return "invalid IOC"

  current_user.blue_points += int(target_user.heat)
  target_user.heat = 0
  target_user.burn()
  db.session.commit()

  return flask.redirect('/')
  #return render_template("burn.html",current_user=current_user,target_user=target_user,ioc=ioc)

# https://medium.com/@perwagnernielsen/getting-started-with-flask-login-can-be-a-bit-daunting-in-this-tutorial-i-will-use-d68791e9b5b5

@app.route('/protected')
@login_required
def protected():
    return "protected area : "+str(current_user.username)

@login_manager.user_loader
def load_user(username):
    return User.query.filter_by(username = username).first()

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if request.method == 'GET':
        return render_template('signup.html', form = form)
    elif request.method == 'POST':
      if form.validate_on_submit():
            if User.query.filter_by(username=form.username.data).first():
                return "user already exists" 
            else:
                newuser = User(form.username.data, form.password.data)
                db.session.add(newuser)
                db.session.commit()
                login_user(newuser)
                return "User created!!!"        
      else:
             return "Form didn't validate"

@app.route('/login', methods=['POST'])
def login():
  form = SignupForm()
  if form.validate_on_submit():
    user=User.query.filter_by(username=form.username.data).first()
    if user:
      #if user.password == form.password.data:
      print(form.password.data)
      print(user.password_hash)
      print(user.salt)
      if check_password_hash(form.password.data, user.password_hash, user.salt):
        login_user(user)
        return flask.redirect('/')
      else:
          return "wrong password"            
    else:
      newuser = User(form.username.data, form.password.data)
      db.session.add(newuser)
      db.session.commit()
      login_user(newuser)
      return flask.redirect('/')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return flask.redirect('/')

