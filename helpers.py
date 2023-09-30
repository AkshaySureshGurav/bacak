import json
import sqlite3
from sqlite3 import Error
from datetime import date


def load_json():
  with open('data.json', "r") as file:
    data = json.load(file)
  return data


def dump_json(x):
  with open('data.json', "w") as file:
    json.dump(x, file, indent=4)


def create_connection(db_file):
  """ create a database connection to a SQLite database """
  conn = None
  print(db_file)
  try:
    conn = sqlite3.connect("static/database/" + db_file + ".db")
    # print(sqlite3.version)
  except Error as e:
    print(e)

  return conn


def makeDB(user):
  print("in makeDB" + user)
  conn = create_connection(user)
  db = conn.cursor()

  db.execute('''CREATE TABLE Accounts
                (ID INTEGER PRIMARY KEY AUTOINCREMENT, name text)''')
  db.execute('''CREATE TABLE cash
                (ID integer, Date text, Balance real)''')
  db.execute('''CREATE TABLE os
                (p_ID INTEGER, Updated_on text, Name text, Amount real, FOREIGN KEY (p_ID) REFERENCES Accounts(ID))'''
             )
  db.execute('''CREATE TABLE expense
                (p_ID INTEGER, Date text, Name text, Amount real, description text, FOREIGN KEY (p_ID) REFERENCES Accounts(ID))'''
             )
  db.execute('''CREATE TABLE osEntry
                (p_ID INTEGER, Date text, Name text, Amount real, description text, FOREIGN KEY (p_ID) REFERENCES Accounts(ID))'''
             )
  db.execute('''CREATE TABLE cashEntries
                (Name text, Date text, Amount real, description text)''')
  conn.commit()
  conn.close()


def get_acc(user):
  print("in get_acc" + user)
  conn = create_connection(user)
  db = conn.cursor()

  db.execute('SELECT name FROM Accounts')
  # Fetch all the rows of the result set
  result = db.fetchall()

  # Loop through the rows and append the values to the array
  array = []
  for row in result:
    # converting the data of list from tuple to str
    # cause the db stores it in tuple form
    array.append(row[0])

  conn.commit()
  conn.close()

  return array


def make_os_entry(user, account_id, amt,
                  description):  #return True if no error else False
  print("in make_os_entry" + user)
  conn = create_connection(user)
  db = conn.cursor()

  # if the user have not selected a name like if it is still default value: None
  try:
    # getting the name of the account with the help of account_id
    acc_name = db.execute("SELECT name FROM Accounts WHERE ID=?;",
                          (account_id, )).fetchall()[0][0]
  except:
    conn.commit()
    conn.close()
    return False

  db.execute(
    "INSERT INTO osEntry (p_ID, Date, name, Amount, description) VALUES (?, ?, ?, ?, ?);",
    (
      account_id,
      date.today(),
      acc_name,
      amt,
      description,
    ))

  arr = db.execute("SELECT Name FROM os WHERE p_ID=?;",
                   (account_id, )).fetchall()

  # if a account already has an past entry then update the existing entry
  if len(arr) > 0:
    amt = amt + (db.execute("SELECT Amount FROM os WHERE p_ID=?;",
                            (account_id, )).fetchall()[0][0])
    db.execute("UPDATE os SET Updated_on=?, Amount=? WHERE p_ID=?;",
               (date.today(), amt, account_id))
  else:
    db.execute(
      "INSERT INTO os (p_ID, Updated_on, Name, Amount) VALUES (?, ?, ?, ?);",
      (account_id, date.today(), acc_name, amt))

  conn.commit()
  conn.close()
  return True


def get_cash_bal(user):
  print("in get_cash_bal = (" + user + " )")
  conn = create_connection(user)
  db = conn.cursor()
  try:
    cash = db.execute("SELECT Balance FROM cash;").fetchall()
    cash = int(cash[0][0])
  except IndexError:
    cash = None
  conn.commit()
  conn.close()
  return cash


def cash_entry(user, From, amount, description):
  print("in cash_entry" + user)
  conn = create_connection(user)
  db = conn.cursor()

  if len(db.execute("SELECT Balance FROM cash;").fetchall()) > 0:
    updated_cash_bal = get_cash_bal(user) + amount
    db.execute("UPDATE cash SET Date=?, Balance=? WHERE ID=1;", (
      date.today(),
      updated_cash_bal,
    ))
  else:
    db.execute("INSERT INTO cash (ID, Date, Balance) VALUES (?, ?, ?);", (
      1,
      date.today(),
      amount,
    ))

  db.execute(
    "INSERT INTO cashEntries (Name, Date, Amount, description) VALUES (?, ?, ?, ?);",
    (
      From,
      date.today(),
      amount,
      "Cash in and description: " + description,
    ))

  conn.commit()
  conn.close()


# def check_col_in_acc(user, column, account):
#     conn = create_connection("C:/Users/Akshay/flaskapp/final/static/database/" + user + ".db")
#     db = conn.cursor()

#     data = db.execute("SELECT ? FROM ?;", (column, account,)).fetchall()

#     conn.commit()
#     conn.close()

#     if len(data) > 0:
#         return True
#     return False


def deduct_from_cash_bal(user, account_id, amt, description):
  print("in deduct_from_cash_bal" + user)
  conn = create_connection(user)
  db = conn.cursor()

  updated_cash_bal = get_cash_bal(user) - amt

  db.execute("UPDATE cash SET balance=? WHERE id=1;", (updated_cash_bal, ))
  # getting the name of the account with the help of account_id
  acc_name = db.execute("SELECT name FROM Accounts WHERE ID=?;",
                        (account_id, )).fetchall()[0][0]

  db.execute(
    "INSERT INTO cashEntries (Name, Date, Amount, description) VALUES (?, ?, ?, ?);",
    (
      acc_name,
      date.today(),
      amt,
      "Cash out. Description - " + description,
    ))

  conn.commit()
  conn.close()


def exp_entry(user, account_id, acc_name, amount, description, acc_os_bal):
  print("in exp_entry" + user)
  conn = create_connection(user)
  db = conn.cursor()
  updated_os_bal = acc_os_bal - amount

  db.execute(
    "INSERT INTO expense (p_ID, Date, name, Amount, description) VALUES (?, ?, ?, ?, ?);",
    (
      account_id,
      date.today(),
      acc_name,
      amount,
      description,
    ))
  db.execute("UPDATE os SET Updated_on=?, Amount=? WHERE p_ID=?;",
             (date.today(), updated_os_bal, account_id))

  conn.commit()
  conn.close()


def printName(name):
  print(name)
