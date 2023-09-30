from flask import Flask, render_template, request, session, flash, redirect
from flask_session import Session
from helpers import load_json, dump_json, makeDB, create_connection, get_acc, make_os_entry, get_cash_bal, cash_entry, deduct_from_cash_bal, exp_entry, printName

app = Flask(__name__)
app.secret_key = "akkiTheRacer"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
    if username != None and password != None:
      json = load_json()
      if username in json.keys() and json[username] == password:
        session["name"] = username
        return redirect("/index")
      else:
        flash("Wrong Username or password.")
        return redirect("/")
    else:
      flash("Username or password can't be empty.")
      return redirect("/")
  else:
    return render_template('login.html')


@app.route("/index")
def index():
  Username = session.get("name")
  return render_template('index.html', user=Username)


@app.route("/logout")
def logout():
  session["name"] = None
  return redirect("/")


@app.route('/register', methods=['GET', 'POST'])
def register():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
    con_password = request.form['con_password']
    if username != "" and password != "" and con_password != "":
      json_file = load_json()
      if username not in json_file:
        if password == con_password:
          json_file.update({username: password})
          dump_json(json_file)

          #Making the required database for storing acccounts
          makeDB(username)
          flash("Account created.")
          return render_template('login.html')
        else:
          flash("Password and confirm password are not same.")
          return redirect("/register")
      else:
        flash("Account already exist with same username.")
        return redirect("/register")
    else:
      flash("Couldn't create an account.")
      return redirect("/register")
  else:
    return render_template('register.html')


@app.route("/makeEntry")
def makeEntry():
  return render_template('editAccount.html')


@app.route("/viewAC")
def viewAC():
  return render_template('viewAC.html')


@app.route("/makeAccount", methods=["GET", "POST"])
def makeAccount():

  # accs = list of accounts
  printName(session.get("name"))
  nqame = session.get("name")
  printName(nqame)

  # get the list of accounts from the user's database
  accs = get_acc(session.get("name"))
  accsLen = len(accs)
  print(accs, accsLen)
  if request.method == "POST":
    name = request.form["user"]
    if name != "" or name != " ":
      # Creating connection with the db file
      db_raw = create_connection(session.get("name"))
      db = db_raw.cursor()

      if len(
          db.execute('SELECT name FROM Accounts WHERE name LIKE ?;',
                     (name, )).fetchall()) == 0:
        db.execute("INSERT INTO Accounts (name) VALUES (?);", (name, ))

        db_raw.commit()
        db_raw.close()

        flash("Account created.")
        return redirect("/makeAccount")
      else:
        flash("Account named \"" + name + "\" already exists!")
        return render_template('makeAccount.html',
                               Accounts=accs,
                               length=accsLen)

    else:
      flash("Account should be alphabetical.")
      return render_template('makeAccount.html', Accounts=accs, length=accsLen)
  else:
    return render_template('makeAccount.html', Accounts=accs, length=accsLen)


@app.route("/updateCashAc", methods=["GET", "POST"])
def updateCashAc():

  if request.method == "POST":
    From = request.form.get("from")
    amt = int(request.form.get("amount"))
    description = request.form.get("description")
    if amt > 0:
      cash_entry(session.get("name"), From, int(amt), description)
      flash("Entry done.")
      return render_template('updateCashAc.html')
    else:
      flash("Amount can't be 0 or negative value.")
      return render_template('updateCashAc.html')
  else:
    return render_template('updateCashAc.html')


@app.route("/about")
def about():
  return render_template('About.html')


@app.route("/howToUse")
def howToUse():
  return render_template('howToUse.html')


@app.route("/osEntry", methods=["GET", "POST"])
def osEntry():
  accs = get_acc(session.get("name"))
  if request.method == "POST":
    account_id = request.form.get("account")
    amt = int(request.form.get("amount"))
    description = request.form.get("description")

    if amt > 0:
      conn = create_connection(session.get("name"))
      db = conn.cursor()
      array = db.execute("SELECT Balance FROM cash;").fetchall()
      conn.commit()
      conn.close()

      if (len(array)):
        if get_cash_bal(session.get("name")) > int(amt):
          isDone = make_os_entry(session.get("name"), account_id, amt,
                                 description)

          if not (isDone):
            flash("Please check the name selected")
            return render_template('osEntry.html',
                                   acc_name=accs,
                                   len=len(accs))

          deduct_from_cash_bal(session.get("name"), account_id, amt,
                               description)
          # Getting the names of all accounts
          # accs = get_acc(session.get("name"))
          flash("Entry done!!!")
          return render_template('osEntry.html', acc_name=accs, len=len(accs))
        else:
          flash("Not enough cash balance")
          return render_template('osEntry.html', acc_name=accs, len=len(accs))
      else:
        flash("No balance in cash account")
        return render_template('osEntry.html', acc_name=accs, len=len(accs))
    else:
      flash("Amount can't be 0 or negative value.")
      return render_template('osEntry.html', acc_name=accs, len=len(accs))
  else:
    if "name" in session.keys():
      return render_template('osEntry.html', acc_name=accs, len=len(accs))
    else:
      return redirect("/")


@app.route("/expense_entry", methods=["GET", "POST"])
def expense_entry():
  if request.method == "POST":
    account_id = request.form.get("account")
    exp_amt = int(request.form.get("amount"))
    description = request.form.get("description")

    conn = create_connection(session.get("name"))
    db = conn.cursor()
    acc_existence = db.execute("SELECT * FROM os WHERE p_ID=?;",
                               (account_id, )).fetchall()
    try:
      balance = db.execute("SELECT Amount FROM os WHERE p_ID=?;",
                           (account_id, )).fetchall()[0][0]
    except IndexError:
      balance = None
    conn.commit()
    conn.close()

    if len(acc_existence) > 0:
      acc_name = acc_existence[0][2]
      if balance >= exp_amt:
        exp_entry(session.get("name"), account_id, acc_name, exp_amt,
                  description, balance)
        flash("Entry Done.")
        return redirect("/expense_entry")

      else:
        flash(
          "Selected account doesn't have that much oustanding balance to be deducted."
        )
        return redirect("/expense_entry")
    else:
      flash("No oustanding balance of the selected account.")
      return redirect("/expense_entry")
    # return render_template('pack2.html', message="Entry done.")
  else:
    if "name" in session.keys():
      accs = get_acc(session.get("name"))
      return render_template('expense_entry.html',
                             acc_name=accs,
                             len=len(accs))
    else:
      return redirect("/")


@app.route("/os_bal_detailed_view")
def os_detailed_view():
  if "name" in session.keys():
    conn = create_connection(session.get("name"))
    db = conn.cursor()
    array = db.execute("SELECT * FROM os ORDER BY Amount DESC;").fetchall()
    os_balance = db.execute("SELECT SUM(Amount) FROM os;").fetchall()[0][0]
    conn.commit()
    conn.close()
    return render_template('os_bal_detailed_view.html',
                           data=array,
                           OS_balance=os_balance)
  else:
    return redirect("/")


@app.route("/os_entry_detailed_view")
def os_entry_detailed_view():
  conn = create_connection(session.get("name"))
  db = conn.cursor()
  array = db.execute("SELECT * FROM osEntry;").fetchall()
  conn.commit()
  conn.close()
  return render_template('os_entry_detailed_view.html', data=array)


@app.route("/cash_detailed_view")
def cash_detailed_view():
  userName = session.get("name")
  conn = create_connection(userName)
  db = conn.cursor()
  array = db.execute("SELECT * FROM cashEntries;").fetchall()
  conn.commit()
  conn.close()
  cashBalance = get_cash_bal(session.get("name"))
  if cashBalance == None:
    flash("No balance yet in cash account.")
    return render_template('updateCashAc.html')

  return render_template('cash_detailed_view.html',
                         data=array,
                         cash_balance=cashBalance)


@app.route("/expense_detailed_view")
def expense_detailed_view():
  conn = create_connection(session.get("name"))
  db = conn.cursor()
  array = db.execute("SELECT * FROM expense;").fetchall()
  conn.commit()
  conn.close()
  return render_template('expense_detailed_view.html', data=array)


app.run(host='0.0.0.0', port=81)
