import re
import datetime

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, formatDistance

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


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///swimTracker.db")


@app.route("/")
@login_required
def index():

    # get users name from database
    rows = db.execute("SELECT firstName FROM users WHERE userid=?", session["user_id"])
    name = rows[0]['firstName']

    # get users preferred units
    units = session["units"]

    # get current year
    today = datetime.datetime.today()
    year = today.strftime("%Y")

    # get total for current year in user preferred units
    command = "SELECT strftime('%Y', date) as year, SUM(" + units + ") FROM swims WHERE userid=? AND year=?"
    row = db.execute(command, session["user_id"], year)

    # format total for display
    cmd = "SUM(" + units + ")"
    total = formatDistance(row[0][cmd])

    return render_template("summary.html", name=name, total=total, units=units, year=year)


@app.route("/logSwims", methods=["GET", "POST"])
@login_required
def logSwims():

    # User reached route via POST (as by submitting a form via POST)

    if request.method == "POST":
        today = datetime.datetime.today()
        # Remove time so it matches user entered format from html
        today = today.replace(hour=00, minute=00, second=00, microsecond=0)

        # Ensure date was submitted
        swimDate = request.form.get("swimDate")
        if not swimDate:
            return apology("must provide date", 400)

        # Check if date is in the future
        swimDate = datetime.datetime.strptime(swimDate, "%Y-%m-%d")
        if swimDate > today:
            return apology("Cannot enter future data!", 400)

        # Ensure distance was submitted
        distance = request.form.get("distance")
        if not distance:
            return apology("must enter distance", 400)

        distance = float(distance)
        if distance <= 0:
            return apology("must enter valid distance")

        units = request.form.get("units")

        yards = meters = miles = 0

        # distance entered in yards
        if units == 'yards':
            yards = distance
            miles = distance / 1760
            meters = distance * 0.9144

        # distance entered in meters
        elif units == 'meters':
            meters = distance
            yards = distance / 0.9144
            miles = distance / 1609.344

        # distance entered in miles
        elif units == 'miles':
            miles = distance
            yards = distance * 1760
            meters = distance * 1609.344

        else:
            return apology("Error with units", 400)

        # Enter swim into database
        db.execute("INSERT INTO swims (userid, date, meters, miles, yards, enteredunits) VALUES(?, ?, ?, ?, ?, ?)",
                    session["user_id"], swimDate, meters, miles, yards, units)

        return redirect("/viewResults")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("logSwims.html")


@app.route("/viewResults", methods=["GET"])
@login_required
def viewResults():

    # get user's swims from the database
    swims = db.execute("SELECT * FROM swims WHERE userid=? ORDER BY date DESC", session["user_id"])

    return render_template("viewResults.html", swims=swims)


@app.route("/monthlyResults", methods=["GET"])
@login_required
def monthlyResults():

    # get users preferred units
    units = session["units"]

    # get monthly totals from database
    command = "SELECT strftime('%Y', date) as year, strftime('%m', date) as month, SUM(" + units + ") " \
              "FROM swims WHERE userid=? GROUP BY year, month ORDER BY year DESC, month DESC"
    monthlyTotals = db.execute(command, session["user_id"])

    # get yearly totals from database
    command = "SELECT strftime('%Y', date) as year, SUM(" + units + ") FROM swims WHERE userid=? " \
              "GROUP BY year ORDER BY year DESC"
    yearTotals = db.execute(command, session["user_id"])

    # format distance for display
    cmd = "SUM(" + units + ")"
    for month in monthlyTotals:
        month['distance'] = formatDistance(month[cmd])
    for year in yearTotals:
        year['distance'] = formatDistance(year[cmd])

    return render_template("monthlyResults.html", units = units, monthlyTotals = monthlyTotals, yearTotals = yearTotals)


@app.route("/editResults", methods=["GET", "POST"])
@login_required
def editResults():

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        deleteSwim = request.form['delete']
        db.execute("DELETE FROM swims WHERE userid=? AND swimid=?", session["user_id"], deleteSwim)
        return redirect("/viewResults")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # get user's swims from the database
        swims = db.execute("SELECT * FROM swims WHERE userid=? ORDER BY date DESC", session["user_id"])
        return render_template("editResults.html", swims=swims)


@app.route("/preferences", methods=["GET", "POST"])
@login_required
def preferences():

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Get units to display totals
        units = request.form['units']

        # Enter units preference into database
        db.execute("UPDATE users SET units=? WHERE userid=?", units, session["user_id"])

        # Remember user's unit preference
        session["units"] = units

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("preferences.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure email was submitted
        if not request.form.get("email"):
            return apology("must provide email", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE email = ?", request.form.get("email"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["userid"]
        # Save user's preferred units in session
        session["units"] = rows[0]["units"]

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


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Get data from form:
        email = request.form.get("email")
        first = request.form.get("first")
        last = request.form.get("last")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        units = request.form['units']

        # Ensure username was submitted
        if not email:
            return apology("must provide email", 400)

        # Ensure first name was submitted
        if not first:
            return apology("must provide first name", 400)

        # Ensure last name was submitted
        if not last:
            return apology("must provide last name", 400)

        # Ensure password was submitted
        if not password:
            return apology("must provide password", 400)

        # Ensure password confirmation was submitted
        if not confirmation:
            return apology("must reenter password to confirm", 400)

        # Query database to check if username already exists
        rows = db.execute("SELECT * FROM users WHERE email = ?", email)

        if len(rows) == 1:
            return apology("email already exists", 400)

        # Check if passwords match
        if password != confirmation:
            return apology("passwords must match", 400)

        # Ensure preferred unitswas submitted
        if not units:
            return apology("must provide preferred units", 400)

        # Check strength of password: must have at least 8 characters, 1 uppercase, 1 lowercase, 1 special character

        # Check length of password
        if len(password) < 8:
            return apology("passwords must have at least 8 characters", 400)

        upperRegex = re.compile(r'[A-Z]')
        lowerRegex = re.compile(r'[a-z]')
        numberRegex = re.compile(r'\d')
        specialRegex = re.compile(r'\W')

        if(upperRegex.search(password) == None):
            return apology("passwords must contain at least 1 uppercase character", 400)

        if(lowerRegex.search(password) == None):
            return apology("passwords must contain at least 1 lowercase letter", 400)

        if(numberRegex.search(password) == None):
            return apology("passwords must contain a least 1 number", 400)

        if(specialRegex.search(password) == None):
            return apology("passwords must contain at least 1 special character", 400)

        # Add user to database
        db.execute("INSERT INTO users (email, hash, firstName, lastName, units) VALUES(?, ?, ?, ?, ?)", email,
                   generate_password_hash(password), first, last, units)

        # Query database to get user's id for session
        rows = db.execute("SELECT * FROM users WHERE email = ?", email)
        session["user_id"] = rows[0]["userid"]

        # Save user's preferred units in session
        session["units"] = rows[0]["units"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

