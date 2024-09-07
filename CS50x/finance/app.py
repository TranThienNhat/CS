import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.sqlite3")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # The user's id in the database
    user_id = session["user_id"]

    # Update stock prices
    name_update = db.execute("SELECT symbol FROM buy WHERE user_id = ? GROUP BY symbol", user_id)

    for item in name_update:
        symbol = item["symbol"]
        db.execute("UPDATE buy SET price = ? WHERE symbol = ?", (lookup(symbol)['price']) , symbol)

    # Update stock total
    total_update = db.execute("SELECT price, shares, buy_id FROM buy WHERE user_id = ?", user_id)

    for item in total_update:
        price = item["price"]
        shares = item["shares"]
        buy_id = item["buy_id"]
        db.execute("UPDATE buy SET total = ? WHERE buy_id = ?", (float(price) * float(shares)), buy_id)

    # Get data form database
    value = db.execute("SELECT symbol, SUM(shares) AS shares, price, SUM(total) AS total FROM buy GROUP BY symbol AND price")
    user_data = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
    cash = user_data[0]["cash"] if user_data else 0

    # Total available value
    total_cash = cash + sum(item["total"] for item in value)

    # Displays the home page
    return render_template("index.html", value=value, cash=cash, total_cash=total_cash, usd=usd)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # Get data from symbols and shares form buy
    symbol = request.form.get("symbol")
    shares = request.form.get("shares")

    # User reached route via POST
    if request.method == "POST":
        # Ensure symbol was submitted
        if not symbol:
            return apology("Missing symbol", 400)

        # Make sure the symbol exists
        elif lookup(symbol) == None:
            return apology("Invaild symbol", 400)

        # Ensure shares was submitted
        elif not shares:
            return apology("Missing shares", 400)

        # Ensure shares is a positive integer
        try:
            shares = int(shares)
            if shares <= 0:
                return apology("Invalid shares", 400)
        except ValueError:
            return apology("Shares must be an integer", 400)

        # Get data from API
        buy_symbol = lookup(symbol)
        price = buy_symbol['price']

        # Get data from database
        user_id = session["user_id"]
        cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]

        # Guaranteed cost < cash
        if float(price) * float(shares )> cash:
            return apology("can't afford", 400)
        else:
            # Fill in the data in the purchase table
            symbol = symbol.upper()

            db.execute("INSERT INTO buy (user_id, symbol, shares, price, total) VALUES (?,?,?,?,?)", user_id, symbol, shares, price, (float(price) * float(shares)))

            db.execute("INSERT INTO history (user_id, symbol, shares, price) VALUES (?,?,?,?)", user_id, symbol, shares, price)

            # Update cash
            db.execute("UPDATE users SET cash = cash - ?", float(price) * float(shares))

        flash("Bought!")

        # Go to home page
        return redirect("/")

    # User reached route via GET
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user_id = session["user_id"]

    value = db.execute("SELECT symbol, shares, price, datetime FROM history WHERE user_id = ?", user_id)

    return render_template("history.html", value=value)



@app.route("/changepass", methods=["GET", "POST"])
@login_required
def changepass():
    """Show changepass"""
    if request.method == "POST":
        oldpass = request.form.get("oldpassword")
        newpass = request.form.get("newpassword")

        if not oldpass:
            return apology("missing password", 400)
        hash = db.execute("SELECT hash FROM users WHERE id = ?", session["user_id"])
        if not check_password_hash(hash[0]["hash"], oldpass):
            return apology("invalid password", 400)
        if not newpass:
            return apology("missing password", 400)
        if newpass != request.form.get("confirmation"):
            return apology("Please confirm your password", 400)

        new_hash = generate_password_hash(newpass)

        db.execute("UPDATE users SET hash = ? WHERE id = ?", new_hash, session["user_id"])

        flash("Password changed!")

        return redirect("/")
    else:
        return render_template("changepass.html")


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
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

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

    # Get data from symbols form quote
    symbol = request.form.get("symbol")

    # User reached route via POST
    if request.method == "POST":
        # Ensure symbol was submitted
        if not symbol:
            return apology("Missing symbol", 400)

        # Make sure the symbol exists
        elif lookup(symbol) == None:
            return apology("invalid symbol", 400)

        # Go to page quoted
        value = lookup(symbol)
        return render_template("quoted.html", value=value, usd=usd)

    # User reached route via GET
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Get data from registration page
    username = request.form.get("username")
    checkuser = db.execute("SELECT * FROM users WHERE username = ?", username)
    password = request.form.get("password")
    confirmation = request.form.get("confirmation")

    # User reached route via POST
    if request.method == "POST":
        # Ensure username was submitted
        if not username:
            return apology("Invalid username", 400)

        # Make sure the username is unique
        if len(checkuser) != 0:
            return apology("username already exists", 400)

        # Ensure password was submitted
        elif not password:
            return apology("Invalid password", 400)

        # Make sure to confirm the password
        if password != confirmation:
            return apology("Please confirm your password", 400)

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Insert password into database
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hashed_password)

        # Make sure that after registering, you can go to the home page
        result = db.execute("SELECT id FROM users WHERE username = ?", username)
        id_of_new_user = result[0]['id']
        session["user_id"] = id_of_new_user

        flash("Registed!")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # The user's id in the database
    user_id = session["user_id"]

    # User reached route via POST
    if request.method == "POST":
        # Get data from sell page
        symbol = request.form.get("symbol")
        shares_str = request.form.get("shares")

        # Ensure symbol was submitted
        if not symbol:
            return apology("Missing symbol", 400)

        try:
            shares = int(shares_str)
            if shares <= 0:
                return apology("Invalid number of shares", 400)
        except ValueError:
            return apology("Invalid number of shares", 400)

        # Get the total shares the user has bought for the given symbol
        total_shares = db.execute("SELECT SUM(shares) AS shares FROM buy WHERE user_id = ? AND symbol = ?", user_id, symbol)

        if total_shares[0]["shares"] is None or shares > total_shares[0]["shares"]:
            return apology("Too many shares", 400)

        # Get the current price of the stock
        stock = lookup(symbol)
        if stock is None:
            return apology("Invalid symbol", 400)

        sell_price = stock["price"]
        total_cash_earned = 0
        total_shares = shares
        symbol = symbol.upper()

        # Loop through the user's shares for the symbol and sell them
        rows = db.execute("SELECT shares, buy_id FROM buy WHERE user_id = ? AND symbol = ?", user_id, symbol)
        for row in rows:
            if shares <= 0:
                break

            sell_shares = min(shares, row["shares"])
            shares -= sell_shares

            # Update the shares in the database
            remaining_shares = row["shares"] - sell_shares
            if remaining_shares > 0:
                db.execute("UPDATE buy SET shares = ? WHERE buy_id = ?", remaining_shares, row["buy_id"])
            else:
                db.execute("DELETE FROM buy WHERE buy_id = ?", row["buy_id"])

            # Calculate the cash earned from this sale
            total_cash_earned += sell_shares * sell_price

        # Update user's cash
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", total_cash_earned, user_id)

        db.execute("INSERT INTO history (user_id, symbol, shares, price) VALUES (?,?,?,?)", user_id, symbol, -total_shares, sell_price)

        flash("Sold!")
        return redirect("/")

    # User reached route via GET
    else:
        symbols = db.execute("SELECT symbol FROM buy WHERE user_id = ? GROUP BY symbol", user_id)
        return render_template("sell.html", symbols=symbols)
