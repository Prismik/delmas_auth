import datetime

class Journal():
  SEVERE = "severe"
  ERROR = "error"
  INFO = "info"
  VERBOSE = "verbose"
  OK = "ok"

  def __init__(self, database):
    self.database = database
    self.logs = []

  def log(self, message, level):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log = { 'timestamp': now, 'msg': message, 'lvl': level }
    print(log)
    self.logs.append(log)
    self.database.insert_log(log)

  def top(self):
    for item in self.logs[-15:]:
      print(item)
