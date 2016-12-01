import flask_login

class DelmasUser(flask_login.UserMixin):
  def __init__(self, name, roles, prev_pwds, blocked_until, nb_attempt, force_pwd_change):
  	print prev_pwds
	self.id = name
	self.roles = roles
	self.previous_passwords = prev_pwds
	newest_pass = prev_pwds[0]
	for p in prev_pwds:
		if p['created_at'] > newest_pass['created_at']:
			newest_pass = p
	self.password = newest_pass
	self.locked_until = blocked_until
	self.nb_attempt = nb_attempt
	self.force_pwd_change = force_pwd_change
	print self
