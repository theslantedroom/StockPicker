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

# for my local env variable and api key

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from operator import itemgetter
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

# for postgress
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI')
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure session to use filesystem (instead of signed cookies)
# app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///finance.db"
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
        return redirect("/")

@app.route("/history")
@login_required
def history():
    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    return render_template("login.html")
@app.route("/logout")
def logout():
    return redirect("/")

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    return redirect("/")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    return redirect("/")


@app.route("/leaderboard", methods=["GET", "POST"])
def leaderboard():  
    return redirect("/")

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
 app.debug = False
 port = int(os.environ.get("PORT", 8080))
 app.run(host="0.0.0.0", port=port)
