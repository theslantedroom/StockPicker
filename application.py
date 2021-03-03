# must run in cmd venv before start
# $Env:FLASK_APP="application.py"
# $Env:FLASK_DEBUG=1

# C:\sqlite\sqlite-tools-win32-x86-3340100\sqlite3.exe finance.db

# CREATE TABLE users (id INTEGER, username TEXT NOT NULL, hash TEXT NOT NULL, cash NUMERIC NOT NULL DEFAULT 100000.00, PRIMARY KEY(id));

# CREATE TABLE 'portfolio' ('id' integer NOT NULL, 'username' text, 'symbol' text NOT NULL, 'stockname' text, 'shares' integer NOT NULL, 'bookcost' real, 'total' real, 'date' datetime NOT NULL DEFAULT CURRENT_TIMESTAMP);

# CREATE TABLE 'history' ('id' integer NOT NULL, 'symbol' text NOT NULL, 'date' datetime NOT NULL DEFAULT CURRENT_TIMESTAMP, 'shares' integer NOT NULL, 'value' numeric NOT NULL );

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

# for postgress of heroku deployment
# db = SQL(os.getenv("DATABASE_URL"))

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

    stocksConverted = stocks
    for key, stock in enumerate(stocks):
        # convert to formated string fro display
        stocksConverted[key][3] = "${:,.2f}".format(stocks[key][3])
        stocksConverted[key][4] = "${:,.2f}".format(stocks[key][4])
        
    cashConverted = "${:,.2f}".format(cash)
    totalConverted = "${:,.2f}".format(total)

    return render_template("index.html", stocks=stocksConverted, cash=cashConverted, total=totalConverted)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")

    if request.method == "POST":
        # store data from buy form
        
        stringAmount = request.form.get("amount")
        if float(stringAmount) < 0:
            return apology("Must buy at least one stock")
        symbol = request.form.get("symbol")
        
        try:
            buyCount = float(stringAmount)
        except:
            return apology("Must buy at least one stock")

        if not lookup(symbol):
            return apology("Could not find the stock")

        Userid = session["user_id"]
        username = str(db.execute("SELECT username FROM users WHERE id = :id", id=Userid)[0]['username'])
        # print(type(username[0]['username'])) = str

        # Calculate total value of the transaction
        bookcost = lookup(symbol)['price']
        company = lookup(symbol)['name']
        totalCost = buyCount * bookcost
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
            db.execute("INSERT INTO portfolio(id, username, symbol, stockname, shares) VALUES (:id, :username, :symbol, :stockname, :shares)", 
                        id=Userid, username=username, symbol=symbol, stockname=company, shares=buyCount)
            # update caluated values
            # bookcost = 0
            # total = 0
        #add to existing holdings
        else:
            newTotal = buyCount
            newTotal += stocktobuy[0]['shares']
            db.execute("UPDATE portfolio SET shares = :shares WHERE id = :id AND symbol = :symbol",
                id=Userid, symbol=symbol, shares=newTotal)

        # update user cash
        remainingCash = currentCash - totalCost
        db.execute("UPDATE users SET cash = :cash WHERE id = :user", cash=remainingCash, user=Userid)

        # Update history table
        db.execute("INSERT INTO history(id, symbol, shares, value) VALUES (:id, :symbol, :shares, :value)",
                id=session["user_id"], symbol=symbol, shares=buyCount, value=totalCost)

        return redirect("/")

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # query database with the transactions history
    rows = db.execute("SELECT * FROM history WHERE id = :id", id=session["user_id"])

    # pass a list of lists to the template page
    history = []
    for row in rows:
        tradeDetails = lookup(row['symbol'])
        trade = list((tradeDetails['symbol'], tradeDetails['name'], row['shares'], "${:,.2f}".format(row['value']), row['date']))
        history.append(trade)
        
    
    # redirect user to index page
    return render_template("history.html", history=history)

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
        # query database with the transactions history
        rows = db.execute("SELECT symbol, shares FROM portfolio WHERE id = :id", id=session["user_id"])

        # create a dictionary with the availability of the stocks
        stocksHeld = {}
        for row in rows:
            stocksHeld[row['symbol']] = row['shares']

        return render_template("sell.html", stocksHeld=stocksHeld)


    if request.method == "POST":
        # collect relevant informations
        sellCount=int(request.form.get("sellCount"))
        symbol=request.form.get("symbol")
        price=lookup(symbol)["price"]
        value=round(price*sellCount)

        # Update portfolio table
        heldbefore = db.execute("SELECT shares FROM portfolio WHERE id = :user AND symbol = :symbol", symbol=symbol, user=session["user_id"])[0]['shares']
        heldafter = heldbefore - sellCount

        # stop the transaction if the user does not have enough stocks
        if heldafter < 0:
            return apology("You hold that stock, but not that many!")

        # delete stock from table if we sold out all stocks
        if heldafter == 0:
            db.execute("DELETE FROM portfolio WHERE id = :user AND symbol = :symbol", symbol=symbol, user=session["user_id"])
        # else update with new count
        else:
            db.execute("UPDATE portfolio SET shares = :shares WHERE id = :user AND symbol = :symbol",
                          symbol=symbol, user=session["user_id"], shares=heldafter)
        #update user's cash
        cash = db.execute("SELECT cash FROM users WHERE id = :user",
                          user=session["user_id"])[0]['cash']
        cashRemaining = cash + (price * sellCount)
        db.execute("UPDATE users SET cash = :cash WHERE id = :user",
                          cash=cashRemaining, user=session["user_id"])
        # Update history table
        db.execute("INSERT INTO history(id, symbol, shares, value) VALUES (:id, :symbol, :shares, :value)",
                id=session["user_id"], symbol=symbol, shares=-sellCount, value=value)

        return redirect("/")


@app.route("/leaderboard", methods=["GET", "POST"])
def leaderboard():  
    
    if request.method == "GET":
        users = db.execute("SELECT username FROM users") 
        listUsers = []
        for user in users:
            userdata = list((user['username'], 0, 0, 'stock','cash','networth'))
            listUsers.append(userdata)
        print('listuser',listUsers)
        # query database for a list of all the users /list of dicts
        
        for user in listUsers:
            holdingValue = 0
            holdings = db.execute("SELECT * FROM portfolio WHERE username = :username", username=user[0])
            cash = db.execute("SELECT cash FROM users WHERE username = :username", username=user[0])[0]['cash']
            user[2] = round(cash,2)
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
                user[1] = round(holdingValue, 2)
                
                # user[1] = round(holdingValue, 2)
            # print('holdingValue ',holdingValue)
        for user in listUsers:
            net = round(user[2] + user[1],0)
            user[3] = "${:,.0f}".format(user[1])
            user[4] = "${:,.0f}".format(user[2])
            user[5] = "${:,.0f}".format(net)

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