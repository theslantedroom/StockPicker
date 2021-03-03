# must run in cmd venv before start
# $Env:FLASK_APP="application.py"
# $Env:FLASK_DEBUG=1

# C:\sqlite\sqlite-tools-win32-x86-3340100\sqlite3.exe finance.db

# CREATE TABLE users (id INTEGER, username TEXT NOT NULL, hash TEXT NOT NULL, cash NUMERIC NOT NULL DEFAULT 100000.00, PRIMARY KEY(id));

# CREATE TABLE 'portfolio' ('id' integer NOT NULL, 'username' text, 'symbol' text NOT NULL, 'stockname' text, 'shares' integer NOT NULL, 'bookcost' real, 'total' real, 'date' datetime NOT NULL DEFAULT CURRENT_TIMESTAMP);

# URI from Herohu Postgres
# postgres://ouvrlcvssdnked:030e4ae2e3fa72acc293d7bd63061b3cb125563b3db8c47f259fa8a6304ecb8c@ec2-54-146-73-98.compute-1.amazonaws.com:5432/d6jhrc78o0fu89

# for Postgress DB later
# import psycopg2
import os
import datetime
x = datetime.datetime.now()
print(x)

# for my local env variable and api key
from dotenv import load_dotenv
project_folder = os.path.expanduser('./')  # adjust as appropriate
load_dotenv(os.path.join(project_folder, '.envVar'))

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
# from flask_sqlalchemy import SQLAlchemy
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")
# print(os.environ['API_KEY'])
os.environ["DEBUSSY"] = "1"


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    userId = session["user_id"]
    # Query  database for INFO
    rows = db.execute("SELECT * FROM portfolio WHERE id = :user",
                          user=userId)
    cash = db.execute("SELECT cash FROM users WHERE id = :user",
                          user=userId)[0]['cash']

    # pass  list of lists to the template page
    total = cash
    stocks = []
    for index, row in enumerate(rows):
        details = lookup(row['symbol'])

        # create a list 
        currentStock = list((details['symbol'], details['name'], row['shares'], details['price'], round(details['price'] * row['shares'], 2)))
        # add the list to the stocks list
        stocks.append(currentStock)
        total += stocks[index][4]

    return render_template("index.html", stocks=stocks, cash=round(cash, 2), total=round(total, 2))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")

    if request.method == "POST":
        # store data from buy form
        amount = float(request.form.get("amount"))
        symbol = request.form.get("symbol")

        if not lookup(symbol):
            return apology("Could not find the stock")
        if not amount:
            return apology("Must buy at least one stock")
        quantity = int(request.form.get("amount"))

        Userid = session["user_id"]
        username = str(db.execute("SELECT username FROM users WHERE id = :id", id=Userid)[0]['username'])
        # print(type(username[0]['username'])) = str

        # Calculate total value of the transaction
        bookcost = lookup(symbol)['price']
        company = lookup(symbol)['name']
        totalCost = amount * bookcost
        print(totalCost)

        print("hello id")
        print(session["user_id"])
        # Check if current CASH is enough
        
        currentCash = db.execute("SELECT cash FROM users WHERE id = :user", user=Userid)[0]['cash']
        print(currentCash)
        if currentCash < totalCost:
            return apology("You don't have enough money")

        # Check if user already owns this stocks 
        stocktobuy = db.execute("SELECT shares FROM portfolio WHERE id = :id AND symbol = :symbol", id=Userid, symbol=symbol)
        print(stocktobuy)

        # Insert new row into the stock table
        if not stocktobuy:
            db.execute("INSERT INTO portfolio(id, username, symbol, stockname, shares) VALUES (:id, :username, :symbol, :stockname, :shares)", id=Userid, username=username, symbol=symbol, stockname=company, shares=amount)
            # update caluated values
            # bookcost = 0
            # total = 0
        #add to existing holdings
        else:
            amount += stocktobuy[0]['shares']
            db.execute("UPDATE portfolio SET shares = :shares WHERE id = :id AND symbol = :symbol",
                id=Userid, symbol=symbol, shares=amount)

        # update user cash
        remainingCash = currentCash - totalCost
        db.execute("UPDATE users SET cash = :cash WHERE id = :user", cash=remainingCash, user=Userid)


        # Update history table
        return redirect("/")
    # return apology("TODO")

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()


    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember user id that has logged in
        session["user_id"] = rows[0]["id"]
        # print("hello id")
        # print(session["user_id"])

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html", stock="")

    if request.method == "POST":
        stock = lookup(request.form.get("stock"))
        if not stock:
            return apology("That stock does not exist")

        return render_template("quote.html", stock=stock)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    if request.method == "POST":
        username = request.form.get('username')
        registerpassword1 = request.form.get('registerpassword1')
        registerpassword2 = request.form.get('registerpassword2')
        PWhash = generate_password_hash(registerpassword1)
        registeredUsers = db.execute("SELECT username FROM users")
    
        print(registeredUsers)

        if not username:
            return apology("no username")
        if not registerpassword1:
            return apology("did not enter password")
        if not registerpassword2:
            return apology("did not enter retyped password")
        if registerpassword1 != registerpassword2 :
            return apology("passwords did not match")

        if db.execute("SELECT * FROM users WHERE username = :username",
            username=request.form.get("username")):
            return apology("Username taken")

        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, PWhash)

        return redirect("/")


    


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "GET":
        stocks = {}
        return render_template("sell.html", stocks=stocks)
    if request.method == "POST":
        return apology("sell")


@app.route("/leaderboard", methods=["GET", "POST"])
def leaderboard():  
    
    if request.method == "GET":
        users = db.execute("SELECT username FROM users") 
        listUsers = []
        for user in users:
            userdata = list((user['username'], 0, 0, 0))
            listUsers.append(userdata)
        print('listuser',listUsers)
        # query database for a list of all the users /list of dicts
        
        for user in listUsers:
            holdingValue = 0
            holdings = db.execute("SELECT * FROM portfolio WHERE username = :username", username=user[0])
            cash = db.execute("SELECT cash FROM users WHERE username = :username", username=user[0])[0]['cash']
            user[2] = cash
            print(user)
            print(holdings) 
            print(cash)
            for stock in holdings:
                # print(stock)
                stockPrice = lookup(stock['symbol'])['price']
                # print('price ',stockPrice)
                value = stock['shares'] * stockPrice
                # print('value ',value)
                holdingValue += value
                user[1] = holdingValue
                
            # print('holdingValue ',holdingValue)
        for user in listUsers:
            user[3] = user[2] + user[1]


   


        
    return render_template("leaderboard.html", listUsers=listUsers)




def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


# for development
# if __name__ == '__main__':
#     app.run(debug=True)


# for production
if __name__ == '__main__':
 app.debug = True
 port = int(os.environ.get("PORT", 8080))
 app.run(host="0.0.0.0", port=port)