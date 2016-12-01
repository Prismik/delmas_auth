import flask_login
import time
 
from datetime import timedelta
from flask import Flask, request, render_template, flash, session
from flask.views import View
from flask import render_template
from lib.user import DelmasUser
from lib.settings import DelmasSettings
from lib.journal import Journal
from lib.delmasdata import DelmasData

app = Flask(__name__)
app.secret_key = 'IFoundThisPasswordInTheGti619Lab'
app.permanent_session_lifetime = timedelta(seconds=10) # TODO give a better time here

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/'
login_manager.refresh_view = '/'
login_manager.session_protection = 'strong'


#---Hash + Salt #1: hashlib.sha256-------------------------------------------------------
import uuid
import hashlib

class Hasher():
  def __init__(self):
    self.nbForHashTimes = 2

  def hash_password(self, password, username):
    # uuid is used to generate a random number
    salt = uuid.uuid4().hex
    print ("Salt for user:" + username + " = " + salt)

    for x in range(0, self.nbForHashTimes):
      password = hashlib.sha256(salt.encode() + password.encode()).hexdigest()

    return password + ':' + salt
    #return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt

  def check_password(self, hashed_password, user_password):
    print(hashed_password)
    password, salt = hashed_password.split(':')
    #return password == hashlib.sha256(salt.encode() + user_password.encode()).hexdigest()

    for x in range(0, self.nbForHashTimes):
      user_password = hashlib.sha256(salt.encode() + user_password.encode()).hexdigest()
    print(password == user_password)
    return password == user_password
  #----------------------------------------------------------------------------------------

# Our mock journalization file
delmas_hasher = Hasher()
delmas_database = DelmasData()
delmas_journal = Journal(delmas_database)
delmas_settings = DelmasSettings(delmas_database)

@app.teardown_appcontext
def close_db(exception):
  delmas_database.close_connection(exception)

# TODO Implement this snippet: http://flask.pocoo.org/snippets/62/
def next_is_valid(next):
  return True

def users_for_frontend():
  frontend_users = {}
  users = delmas_database.get_users(None)
  for key, value in users.iteritems():
    frontend_users[key] = { 'role': value['roles'] }

  return frontend_users
  
@login_manager.user_loader
def user_loader(email):
  users = delmas_database.get_users(email)
  if email not in users:
    return None
  
  #users = delmas_database.get_users(email)
  temp_user = users[email]
  user = DelmasUser(email, temp_user['roles'], temp_user['passwords'], temp_user['locked_until'], temp_user['nbTentatives'], temp_user['forcePwdChange'])
  return user

@login_manager.request_loader
def request_loader(request):
  email = request.form.get('email')
  users = delmas_database.get_users(email)
  if email not in users:
    return

  temp_user = users[email]
  user = DelmasUser(email, temp_user['roles'], temp_user['passwords'], temp_user['locked_until'], temp_user['nbTentatives'], temp_user['forcePwdChange'])

  # DO NOT ever store passwords in plaintext and always compare password
  # hashes using constant-time comparison!
  user.is_authenticated = request.form['pwd'] == user.password

  return user

@app.route("/")
def home():
  if not hasattr(flask_login.current_user, 'id'):
    return render_template('home.html', user='anonymous')
  else:
    connectedUser=flask_login.current_user
    return render_template('home.html', user=connectedUser.id, role=connectedUser.roles)

def password_challenge(user, new_pwd):
  previous_passwords = user.previous_passwords
  if delmas_settings.validate_password(new_pwd, previous_passwords,delmas_hasher):
    # TODO Figure something out
    delmas_database.add_new_password(user.id, delmas_hasher.hash_password(new_pwd, user.id), 'sha256*2')
    delmas_journal.log('Success password change on ' + user.id, Journal.OK)
    return True
  else:
    delmas_journal.log('Failed password change on ' + user.id, Journal.ERROR)
    return False
    

def login_challenge(email, pwd):
  users = delmas_database.get_users(email)
  if email not in users:
    delmas_journal.log('Failed connection on ' + email, Journal.ERROR)
    flash('Bad credentials', 'error')
    return False
    
  temp_user = users[email]
  user = DelmasUser(email, temp_user['roles'], temp_user['passwords'], temp_user['locked_until'], temp_user['nbTentatives'], temp_user['forcePwdChange'])

  print(int(time.time()))
  if int(time.time()) - user.locked_until <= 0:
    delmas_journal.log('Failed connection on ' + email, Journal.ERROR)
    flash('Too many failed attempts', 'error')
    return False
  elif user.nb_attempt >= delmas_settings.auth_max_attempt:
    # TODO Update
    user.locked_until = 0
    user.nb_attempt = 0
    delmas_database.update_user(user)

  hashed_password = user.password['pwd']
  if not delmas_hasher.check_password(hashed_password, pwd):
    delmas_journal.log('Failed connection on ' + email, Journal.ERROR)
    # TODO Update
    user.nb_attempt = user.nb_attempt + 1;
    if user.nb_attempt >= delmas_settings.auth_max_attempt:
      user.locked_until = int(time.time()) + delmas_settings.auth_attempt_timespan.seconds
      delmas_journal.log('User ' + email + ' has been blocked', Journal.INFO)
     
    delmas_database.update_user(user)
    flash('Bad credentials', 'error')
    return False

  return True

@app.route("/login", methods=['POST'])
def login():
  email = request.form.get("mail")
  pwd = request.form.get("pwd")
  if login_challenge(email, pwd):
    users = delmas_database.get_users(email)
    temp_user = users[email]
    delmas_user = DelmasUser(email, temp_user['roles'], temp_user['passwords'], temp_user['locked_until'], temp_user['nbTentatives'], temp_user['forcePwdChange'])
    flask_login.login_user(delmas_user)
    session.permanent = True
    flash('Logged in successfully.')
    # TODO Update value
    delmas_user.nb_attempt = 0
    delmas_database.update_user(delmas_user)
    next = request.args.get('next')

    # next_is_valid should check if the user has valid
    # permission to access the `next` url
    if not next_is_valid(next):
      delmas_journal.log('Failed connection on ' + delmas_user.id, Journal.ERROR)
      return flask.abort(400)

    delmas_journal.log('Successful connection on ' + delmas_user.id, Journal.OK)
    return render_template('home.html', user=delmas_user.id, role=delmas_user.roles)
  else:    
    return render_template('home.html', user='anonymous')

@app.route('/logout')
def logout():
  email = flask_login.current_user.id
  flask_login.logout_user()
  flash('Successfully logged out')
  delmas_journal.log('Successful logout on ' + email, Journal.OK)
  return render_template('home.html', user='anonymous')

@app.route("/square")
@flask_login.login_required
def square():
  connectedUser=flask_login.current_user
  if 'admin' in connectedUser.roles or 'square' in connectedUser.roles:
    return render_template('square.html', user=connectedUser.id, role=connectedUser.roles)
  else:
    flash('Not authorized', 'error')
    return render_template('home.html', user=connectedUser.id, role=connectedUser.roles)

@app.route("/circle")
@flask_login.login_required
def circle():
  connectedUser=flask_login.current_user
  if 'admin' in connectedUser.roles or 'circle' in connectedUser.roles:
    return render_template('circle.html', user=connectedUser.id, role=connectedUser.roles)
  else:
    flash('Not authorized', 'error')
    return render_template('home.html', user=connectedUser.id, role=connectedUser.roles)

@app.route("/admin")
@flask_login.fresh_login_required
def admin():
  connectedUser=flask_login.current_user
  if 'admin' in connectedUser.roles:
    return render_template('admin.html', user=connectedUser.id, role=connectedUser.roles, settings=delmas_settings.settings_for_frontend())
  else:
    flash('Not authorized', 'error')
    return render_template('home.html', user=connectedUser.id, role=connectedUser.roles)

@app.route("/users")
@flask_login.fresh_login_required
def users():
  connectedUser = flask_login.current_user
  if 'admin' in connectedUser.roles:
    return render_template('users.html', user=connectedUser.id, role=connectedUser.roles, user_list=users_for_frontend())
  else:
    flash('Not authorized', 'error')
    return render_template('home.html', user=connectedUser.id, role=connectedUser.roles)

@app.route("/users/create", methods=['POST'])
@flask_login.fresh_login_required
def create_user():
  connectedUser = flask_login.current_user
  if 'admin' in connectedUser.roles:
    email = request.form.get('id')
    pwd = request.form.get('pwd')
    temp_users = delmas_database.get_users(email)
    if email not in temp_users and delmas_settings.validate_password(pwd, [], delmas_hasher):
      role = request.form.get('role')
      delmas_database.create_user(email, delmas_hasher.hash_password(pwd, email), 'sha256*2', [role] )
      flash('User created successfully')
    else:
      flash('Failed to create user')

    return render_template('users.html', user=connectedUser.id, role=connectedUser.roles, user_list=users_for_frontend())
  else:
    flash('Not authorized', 'error')
    return render_template('home.html', user=connectedUser.id, role=connectedUser.roles)

@app.route("/new_password")
@flask_login.fresh_login_required
def new_password():
  connectedUser = flask_login.current_user
  return render_template('change_password.html', user=connectedUser.id, role=connectedUser.roles)

@app.route("/change_password", methods=['post'])
@flask_login.fresh_login_required
def change_password():
  connectedUser = flask_login.current_user
  # TODO Use current password and check if its good
  # TODO Check if pwd + validate match
  curEmail = connectedUser.id

  cur_pwd = request.form.get('cur_pwd')
  new_pwd = request.form.get('new_pwd')
  validate = request.form.get('new_pwd_confirm')
  users = delmas_database.get_users(curEmail)
  temp_user = users[curEmail]
  delmas_user = DelmasUser(curEmail, temp_user['roles'], temp_user['passwords'], temp_user['locked_until'], temp_user['nbTentatives'], temp_user['forcePwdChange'])
  hashed_password = delmas_user.password['pwd']
  if delmas_hasher.check_password(hashed_password, cur_pwd) and password_challenge(connectedUser, new_pwd):
    flash('Password succesfully changed')
    return render_template('home.html', user=connectedUser.id, role=connectedUser.roles)
  else:
    flash('Password could not be changed')
    return render_template('change_password.html', user=connectedUser.id, role=connectedUser.roles)

@app.route("/top")
def top():
  delmas_journal.top()
  if not hasattr(flask_login.current_user, 'id'):
    return render_template('home.html', user='anonymous')
  else:
    connectedUser = flask_login.current_user
    return render_template('home.html', user=connectedUser.id, role=connectedUser.roles)

@app.route("/db_test")
def db_test():
  print "hello buddy"
  useremail = 'test3@delmas.com';
  delmas_database.create_user(useremail,delmas_hasher.hash_password('secret',useremail),'sha256*2',['admin','circle'])
  print delmas_database.get_users(None)
  return render_template('home.html', user='anonymous')

@app.route("/admin/options", methods=['POST'])
@flask_login.fresh_login_required
def options():
  connectedUser = flask_login.current_user
  if 'admin' in connectedUser.roles:
    errors = delmas_settings.set_settings_from_frontend(request.form)
    if errors:
      delmas_journal.log('Failed admin settings change on ' + connectedUser.id, Journal.ERROR)
      flash(errors, 'error')
    else:
      delmas_journal.log('Success admin settings change on ' + connectedUser.id, Journal.OK)
      flash('Mis a jour avec succes')
    return render_template('admin.html', user=connectedUser.id, role=connectedUser.roles, settings=delmas_settings.settings_for_frontend())
  else:
    flash('Not authorized', 'error')
    return render_template('home.html', user=connectedUser.id, role=connectedUser.roles)

if __name__ == "__main__":
  app.run()
