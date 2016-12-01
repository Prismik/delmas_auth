from datetime import timedelta
import re

def compare_pwd(first, second):
  if first['created_at'] > second['created_at']:
    return 1
  elif first['created_at'] == second['created_at']:
    return 0
  else:  #x.resultType < y.resultType
    return -1

class DelmasSettings:
  def __init__(self, database):
    self.database = database
    self.auth_max_attempt = 3
    self.auth_attempt_timespan = timedelta(seconds=5)
    self.pwd_len = 8
    self.pwd_should_contain_digit = True
    self.pwd_should_contain_special_char = False
    self.pwd_should_contain_upper_and_lower = True
    self.pwd_num_previous_pwd_cannot_match = 5

  def refresh_self(self):
    settings = self.database.get_settings()
    self.auth_max_attempt = settings['auth_max_attempt']
    self.auth_attempt_timespan = timedelta(seconds=5)
    self.pwd_len = settings['pwd_len']
    self.pwd_should_contain_digit = settings['should_contain_digit']
    self.pwd_should_contain_special_char = settings['should_contain_special']
    self.pwd_should_container_upper_and_lower = settings['should_contain_upper_lower']
    self.pwd_num_previous_pwd_cannot_match = settings['pwd_prev_not_allowed']

  def validate_password(self, password, previous_passwords, hasher):
    self.refresh_self()
    valid = True
    
    previous_passwords.sort(compare_pwd)
    temp = list(map(lambda old_pwd: old_pwd['pwd'], previous_passwords))
    matched = filter(lambda old_pwd: hasher.check_password(old_pwd, password), temp[-self.pwd_num_previous_pwd_cannot_match:])
    if matched:
      valid = False
      
    if len(password) < self.pwd_len:
      valid = False
      #errors += "Le mot de passe doit avoir au moins " + self.pwd_len + " caracteres; "
    
    if self.pwd_should_contain_digit and not re.match(r".*[0-9].*", password):
      valid = False
      #errors += "Le mot de passe doit avoir au moins chiffre; "
    
    if self.pwd_should_contain_special_char and not re.match(r".*[^a-zA-Z0-9].*", password):
      valid = False
      #errors += "Le mot de passe doit avoir un caractere special; "
      
    if self.pwd_should_contain_upper_and_lower and not (re.match(r".*[A-Z].*", password) and re.match(r".*[a-z].*", password)):
      valid = False
      #errors += "Le mot de passe doit avoir au moins un caractere majuscule et un caractere minuscule; "
    
    return valid

  def settings_for_frontend(self):
    self.refresh_self()
    frontend_settings = {}
    frontend_settings["auth_max_attempt"] = self.auth_max_attempt
    frontend_settings["auth_attempt_timespan"] = self.auth_attempt_timespan.seconds
    frontend_settings["pwd_len"] = self.pwd_len
    frontend_settings["pwd_should_contain_digit"] = self.pwd_should_contain_digit
    frontend_settings["pwd_should_contain_special_char"] = self.pwd_should_contain_special_char
    frontend_settings["pwd_should_contain_upper_and_lower"] = self.pwd_should_contain_upper_and_lower
    frontend_settings["pwd_num_previous_pwd_cannot_match"] = self.pwd_num_previous_pwd_cannot_match
    return frontend_settings
    
  def set_settings_from_frontend(self, form):
    errors = ""
    
    if not int(form.get("auth_max_attempt")) or int(form.get("auth_max_attempt")) < 1:
      errors += "Il faut au minimum une tentative maximum; "
     
    if not int(form.get("auth_attempt_timespan")) or int(form.get("auth_attempt_timespan")) < 0:
      errors += "Le temps d'attente doit etre positif; "
      
    if not int(form.get("pwd_len")) or int(form.get("pwd_len")) < 4:
      errors += "Un mot de passe doit au minimum avoir 4 caracteres; "
      
    if not errors:
      self.auth_max_attempt = int(form.get("auth_max_attempt"))
      self.auth_attempt_timespan = timedelta(seconds=int(form.get("auth_attempt_timespan")))
      self.pwd_len = int(form.get("pwd_len"))
      self.pwd_should_contain_digit = bool(form.get("pwd_should_contain_digit"))
      self.pwd_should_contain_special_char = bool(form.get("pwd_should_contain_special_char"))
      self.pwd_should_contain_upper_and_lower = bool(form.get("pwd_should_contain_upper_and_lower"))
      self.pwd_num_previous_pwd_cannot_match = form.get("reutilisation")
      self.database.update_settings(self)
    
    return errors
