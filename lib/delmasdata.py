import sqlite3
import time
import datetime
from flask import g
    
class DelmasData():
  def __init__(self):
    self.database = './sql/delmas.db'
    self.db = None

  def get_db(self):
    self.db = getattr(g, '_database', None)
    if self.db is None:
      g._database = sqlite3.connect(self.database)
      g._database.row_factory = sqlite3.Row
      g._database.text_factory = str
      self.db = g._database

    return self.db

  def close_connection(self, exception):
    self.db = getattr(g, '_database', None)
    if self.db is not None:
      self.db.close()

  def query_users(self, email):
    query = 'SELECT * FROM users WHERE email = :email' if email is not None else 'SELECT * FROM users'
    # possible optimisation here ?
    cur = self.get_db().execute(query, { "email": email }) if email is not None else self.get_db().execute(query)
    users = cur.fetchall()
    cur.close()
    return users

  def query_user_pwds(self, user):
    query = 'SELECT created_at, pwd, hash_method FROM passwords WHERE user  = :email'
    cur = self.get_db().execute(query, { "email": user["email"] })
    pwds = cur.fetchall()
    cur.close()
    return pwds

  def query_user_roles(self, user):
    query = 'SELECT role FROM user_roles WHERE user  = :email'
    cur = self.get_db().execute(query, { "email":user["email"] })
    roles = cur.fetchall()
    cur.close()
    return roles
    
  def get_users(self, email):
    users = self.query_users(email)
    res = {}
    for user in users:
      pwds = self.query_user_pwds(user)
      roles = self.query_user_roles(user)
      delmas_user = {
        'locked_until': user['locked_until'], 
        'nbTentatives': user['current_connect_attemp'], 
        'forcePwdChange': user['force_pwd_change'], 
        'passwords': [], 
        'roles':[]
      }
      # Map password fields & roles
      delmas_user['passwords'] = list(map(lambda pwd: 
        { 'pwd': pwd['pwd'], 'created_at': pwd['created_at'], 'hashMethod': pwd['hash_method'] }, pwds
      ))
      delmas_user['roles'] = list(map(lambda role: role['role'], roles))

      res[user["email"]] = delmas_user

    return res

  def query_settings(self):
    query = 'SELECT * FROM app_settings ORDER BY created_at DESC;'
    cur = self.get_db().execute(query)
    settings = cur.fetchone()
    cur.close()
    return settings

  def get_settings(self):
    settings = self.query_settings() 
    delmas_settings = {
      'auth_max_attempt': settings['pwd_max_attempts'], 
      'auth_attempt_timespan': settings['pwd_wait_time'], 
      'pwd_len': settings['pwd_min_length'], 
      'should_contain_digit': True if settings['pwd_digit'] == 1 else False, 
      'should_contain_special': True if settings['pwd_special_char'] == 1 else False,
      'should_contain_upper_lower': True if settings['pwd_lower_and_upper'] == 1 else False,
      'pwd_prev_not_allowed': settings['pwd_forbid_x_last'], 
    }
    return delmas_settings
    
  def update_settings(self, settings):
    now = int(time.time())
    print(now)
    query = "INSERT INTO app_settings VALUES ('admin@delmas.com'," + str(now) + ", "
    query += str(settings.auth_max_attempt) + ', 50, 0, 1000, 0, '
    query += str(settings.pwd_num_previous_pwd_cannot_match) + ', ' + str(settings.pwd_len) + ', '
    query += '1' if settings.pwd_should_contain_upper_and_lower else '0'
    query += ', '
    query += '1' if settings.pwd_should_contain_special_char else '0'
    query += ', '
    query += '1' if settings.pwd_should_contain_digit else '0'
    query += ", 'sha256*2')"
    print(query)
    cur = self.get_db().execute(query)
    self.get_db().commit()
    cur.close()

  def insert_log(self, log):
    query = "INSERT INTO logs VALUES ('" + log['lvl'] + "','" + log['timestamp'] + "','" + log['msg'] + "')"
    cur = self.get_db().execute(query)
    self.get_db().commit()
    cur.close()

  def create_user(self, email, password, hash_method ,roles):
    userQuery = 'Insert into users values( :email, 0, 0, null )'
    roleQuery = 'Insert into user_roles values( :email, :role )'
    passQuery = 'Insert into passwords values( :email, :date, :password, :hashmethod)'
    cur = self.get_db().execute(userQuery, {'email':email})
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    self.get_db().execute(passQuery, {'email':email, 'date':now, 'password':password,'hashmethod':hash_method})
    for role in roles:
      self.get_db().execute(roleQuery, {'email':email, 'role':role})
    self.get_db().commit()
    cur.close()

  def add_new_password(self, email, password, hash_method):
    passQuery = 'Insert into passwords values( :email, :date, :password, :hashmethod)'
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = self.get_db().execute(passQuery, {'email':email, 'date':now, 'password':password,'hashmethod':hash_method})
    self.get_db().commit()
    cur.close()

  def update_user(self, delmas_user):
    userQuery = 'Update users set current_connect_attemp = :curAttempts, force_pwd_change = :forceChange, locked_until = :lockedUntil where email = :email'
    cur = self.get_db().execute(userQuery, {'email':delmas_user.id, 'curAttempts':delmas_user.nb_attempt,'forceChange':delmas_user.force_pwd_change,'lockedUntil':delmas_user.locked_until})
    self.get_db().commit()
    cur.close()