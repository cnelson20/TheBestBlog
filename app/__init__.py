import os
import sqlite3
from flask import Flask, render_template, request, session, redirect
from random import randint

MAIN_DB = "blogs.db"

# Creation of db file
db = sqlite3.connect(MAIN_DB)
c = db.cursor()

# Blog table creation
c.execute("""
CREATE TABLE IF NOT EXISTS BLOGS (
    ROWID   INTEGER PRIMARY KEY,
    NAME    TEXT    NOT NULL,
    AUTHOR  TEXT    NOT NULL,
    BID     INTEGER NOT NULL

);""")

# User table creation
c.execute("""
CREATE TABLE IF NOT EXISTS USERS (
    ROWID       INTEGER PRIMARY KEY,
    USERNAME    TEXT    NOT NULL,
    HASH        TEXT    NOT NULL
);""")
db.commit()
db.close()

app = Flask(__name__)
app.secret_key = os.urandom(32)

def isAlphaNum(string):
    """
    returns whether a string is alphanumeric
    """
    for char in string:
        o = ord(char)
        if not ((0x41 <= o <= 0x5A) or (0x61 <= o <= 0x7A) or (0x30 <= o <= 0x39)):
            return False;
    return True;

# Function to render homepage
@app.route("/")
def home_page():
    """
        Homepage
    """
    return render_template("index.html", user=session.get('username'))


# Signup function
@app.route("/signup", methods=['GET', 'POST'])
def signup():
    """
        If method = GET, render page to new username & password
        If method = POST, attempts to sign up user, if successful renders login data
    """
    # Obtaining query from html form
    if request.method == "POST":
        # Checking if required values in query exist using key values
        if 'username' in request.form and 'password' in request.form:
            db = sqlite3.connect(MAIN_DB)
            c = db.cursor()
            # Obtaining data from database
            c.execute("""SELECT USERNAME FROM USERS WHERE USERNAME = ?;""",
                      (request.form['username'],))
            exists = c.fetchone()
            # Checking to see if the username that the person signing up gave has not been made
            if (exists == None):
                username = (request.form['username']).encode('utf-8')
                # Check to see if user follows formatting
                if isAlphaNum(username.decode('utf-8')) == None:
                    db.close()
                    return render_template("login.html", user=session.get('username'), action="/signup", name="Sign Up", error="Username can only contain alphanumeric characters and underscores.")
                # Check to see if username is of proper length
                if len(username) < 5 or len(username) > 15:
                    db.close()
                    return render_template("login.html", user=session.get('username'), action="/signup", name="Sign Up", error="Usernames must be between 5 and 15 characters long")
                password = request.form['password']
                # Checking for illegal characters in password
                if ' ' in list(password) or '\\' in list(password):
                    db.close()
                    return render_template("login.html", user=session.get('username'), action="/signup", name="Sign Up", error="Passwords cannot contain spaces or backslashes.")
                password = str(password)
                # Checking to see if password follows proper length
                if len(password) > 7 and len(password) <= 50:
                    c.execute("""INSERT INTO USERS (USERNAME,HASH) VALUES (?,?)""",
                              (request.form['username'], password,))
                    db.commit()
                    c.execute(
                        """SELECT USERNAME FROM USERS WHERE USERNAME = ?;""", (request.form['username'],))
                    exists = c.fetchone()
                    db.close()
                    if (exists != None):
                        return render_template("login.html", user=session.get('username'), action="/login", name="Login", error="Signed up successfully!")
                    else:
                        return render_template("login.html", user=session.get('username'), action="/signup", name="Sign Up", error="Some error occurred. Please try signing up again.")
                else:
                    db.close()
                    return render_template("login.html", user=session.get('username'), action="/signup", name="Sign Up", error="Password must be between 8 and 50 characters long")
            else:
                db.close()
                return render_template("login.html", user=session.get('username'), action="/signup", name="Sign Up", error="Username already exists")
        else:
            return render_template("login.html", user=session.get('username'), action="/signup", name="Sign Up", error="Some error occurred. Please try signing up again.")
    else:
        return render_template("login.html", user=session.get('username'), action="/signup", name="Sign Up")


@app.route("/login", methods=['GET', 'POST'])
def login():
    """
        If method = GET, render page to enter login info
        If method = POST, attempts to login user with posted data
    """
    if request.method == "POST":
        if 'username' in session:
            return render_template("index.html", user=session.get('username'), message="Already logged in!")
        if 'username' in request.form and 'password' in request.form:
            db = sqlite3.connect(MAIN_DB)
            c = db.cursor()
            c.execute("""SELECT HASH FROM USERS WHERE USERNAME = ?;""",
                      (request.form['username'],))
            hashed = c.fetchone()  # [0]
            db.close()
            if (hashed == None):
                return render_template("login.html", user=session.get('username'), name="Login", action="/login", error="User does not exist.")
            else:
                if hashed[0] == request.form['password']:
                    session['username'] = request.form['username']
                    return render_template("index.html", user=session.get('username'), message="Logged in!")
                else:
                    return render_template("login.html", user=session.get('username'), name="Login", action="/login", error="Password is incorrect")
        else:
            return render_template("login.html", user=session.get('username'), name="Login", action="/login", error="An error occurred. Please try logging in again.")
    else:
        return render_template("login.html", user=session.get('username'), action="/login", name="Login")


# Logout function
@app.route("/logout")
def logout():
    """ 
        Logouts user 
    """
    session.pop('username', default=None)
    return redirect("/")


@app.route("/edit",methods=["GET","POST"])
def edit_blog():
    """
        If method is get, this returns a page where the user can choose which entry to edit 
        If method is POST, takes data and edits page
        If a user isn't logged in or they try to edit someone else's blog, renders an error message
    """
    if 'username' in session and session['username'] == request.args['a']:
        if request.args['a'] != session['username']:
            return render_template("index.html", user=session.get('username'), message="You can only edit your own blogs!")
        if request.method == "POST":
            db = sqlite3.connect(MAIN_DB)
            c = db.cursor()
            print(request.args)
            c.execute("""SELECT ROWID FROM BLOGS WHERE AUTHOR = ? AND BID = ?;""",(request.args['a'],request.args['id'],))
            filename = "blogs/" + str(c.fetchone()[0]) + ".txt" 
            f = open(filename,'r')
            entries = f.read().split("\n\t\t\t\t\t\t\t\t\n")
            f.close()
            print(request.form["edit_blog_contents"])
            entries[int(request.form["edit_bid"])] = request.form["edit_blog_contents"]
            f = open(filename,'w')
            seperator = "\n\t\t\t\t\t\t\t\t\n"
            f.write(seperator.join(entries).replace("\r",""))
            f.close()
            db.close()
            return redirect("/view?a=" + request.args['a'] + "&id=" + request.args['id'])
        else:
            if 'a' in request.args and 'id' in request.args:
                db = sqlite3.connect(MAIN_DB)
                c = db.cursor()
                c.execute("SELECT ROWID FROM BLOGS WHERE AUTHOR = ? AND BID = ?;",(request.args['a'],request.args['id'],))
                blog_id = c.fetchone()[0]
                c.execute("SELECT NAME FROM BLOGS WHERE AUTHOR = ? AND BID = ?;",(request.args['a'],request.args['id'],))
                blog_name = c.fetchone()[0]
                db.close()
                f = open("blogs/"+ str(blog_id) +".txt")
                blog_contents = f.read().split("\n\t\t\t\t\t\t\t\t\n")
                for entry in blog_contents:
                    string = ""
                return render_template("edit.html", name = blog_name, contents = blog_contents, num_entries = len(blog_contents), author = request.args['a'], bid = request.args['id'])
            else:
                return redirect("/")
    return render_template("index.html", message="Must be logged in to edit a blog!")
    

# Code to view all blogs/blogs for one user
@app.route("/all")
def all_blogs():
    """
        If route has no get arguments, return all blogs from the site 
        If route includes '?a=t', return user's blogs only
    """
    results = list()
    db = sqlite3.connect(MAIN_DB)
    c = db.cursor()

    my = False
    # my_blog function
    if (request.args.get('a') == 't' and 'username' in session):
        c.execute("SELECT * FROM BLOGS WHERE AUTHOR = ?;",
                  (session['username'],))
        results = c.fetchall()
        my = True
    else:
        c.execute("SELECT * FROM BLOGS;")
        results = c.fetchall()
    db.close()

    return render_template("all.html", user=session.get('username'), my=my, blogs=results)


@app.route("/random")
def random_blog():
    """
        Redirect user to a random blog 
    """
    db = sqlite3.connect(MAIN_DB)
    c = db.cursor()
    c.execute("SELECT * FROM BLOGS")
    allRows = c.fetchall()
    if (len(allRows) == 0):
        return redirect("/")
    chosenRow = randint(0, len(allRows)-1)
    bid = allRows[chosenRow][3]
    author = allRows[chosenRow][2]

    db.close()
    return redirect("/view?a=" + author + "&id=" + str(bid))


@app.route("/view")
def view_blog():
    """ 
        - Fetches filename from SQL database for given user and BID
        - Renders contents of file using jinja2 templating
    """
    if ('a' in request.args and 'id' in request.args):
        db = sqlite3.connect(MAIN_DB)
        c = db.cursor()
        c.execute("SELECT ROWID FROM BLOGS WHERE AUTHOR = ? AND BID = ?",
                  (request.args['a'], request.args['id']))
        f = c.fetchone()
        c.execute("SELECT NAME FROM BLOGS WHERE AUTHOR = ? AND BID = ?",
                  (request.args['a'], request.args['id']))
        name = c.fetchone()[0]
        db.close()
        if (f != None):
            f = "blogs/" + str(f[0]) + ".txt"
            file = open(f,"r")
            entries = file.read().split("\n\t\t\t\t\t\t\t\t\n")
            entrieslines = list()
            for entry in entries:
                entrieslines.append(entry.split('\n'))
            return render_template("view.html", user=session.get('username'), title=name, blog_id=request.args['id'], byUser=request.args['a'], blog_content=entrieslines)
    return render_template("index.html", user=session.get('username'), message="Blog doesn't exist!")


@app.route("/create", methods=['GET', 'POST'])
def create_blog():
    """ 
        If user is logged in:
        if method = GET render a page to input the blogs name and the first entry
        if method = POST create the blog and redirect them to said blog
    """
    if 'username' in session:
        if request.method == "POST":
            if (len(request.form['name']) > 30):
                return render_template("create.html", user=session.get('username'))
            if (len(request.form['contents']) > 6000):
                return render_template("create.html", user=session.get('username'))
            db = sqlite3.connect(MAIN_DB)
            c = db.cursor()
            c.execute("""SELECT ROWID FROM BLOGS WHERE AUTHOR = ?;""",
                      (session['username'],))
            bid = 0
            while (c.fetchone() != None):
                bid += 1
            c.execute("""INSERT INTO BLOGS (NAME,AUTHOR,BID) VALUES (?,?,?);""",
                      (request.form['name'], session['username'], bid,))
            c.execute("""SELECT ROWID FROM BLOGS WHERE AUTHOR = ? AND BID = ?;""",
                      (session['username'], bid,))
            filename = "blogs/" + str(c.fetchone()[0]) + ".txt"
            db.commit()
            db.close()
            file = open(filename, "wt")
            file.write(request.form['contents'])
            file.close()
            return redirect("/view?a=" + str(session['username']) + "&id=" + str(bid))
        return render_template("create.html", user=session.get('username'))
    return render_template("index.html", message="Must be logged in to create a blog!")


@app.route("/update", methods=['GET', 'POST'])
def update_blog():
    """ 
        If user is logged in:
        if method = GET render a page choose a blog to update and type a new entry
        if method = POST create the blog and redirect them to said blog
    """
    if 'username' in session:
        db = sqlite3.connect(MAIN_DB)
        c = db.cursor()
        c.execute("""SELECT ROWID FROM BLOGS WHERE AUTHOR = ?;""",
                  (session['username'],))
        if (c.fetchone() == None):
            db.close()
            return render_template("index.html", user=session.get('username'), message="You have no blogs!")

        if request.method == "POST":
            c.execute("""SELECT ROWID FROM BLOGS WHERE AUTHOR = ? AND BID = ?;""",
                      (session['username'], int(request.form['bid']),))
            filename = "blogs/" + str(c.fetchone()[0]) + ".txt"
            db.close()
            print(filename)
            file = open(filename, "a")
            file.write("\n\t\t\t\t\t\t\t\t\n")
            file.write(request.form['contents'])
            file.close()
            return redirect("/view?a=" + str(session['username']) + "&id=" + request.form['bid'])

        c.execute("""SELECT * FROM BLOGS WHERE AUTHOR = ?;""",
                  (session['username'],))
        blogs = c.fetchall()
        db.close()
        selectedid = request.args.get('s')
        if selectedid == None:
            selectedid = -1
        else:
            selectedid = int(selectedid)

        return render_template("update.html", user=session.get('username'), blogs=blogs, selectedid=selectedid)

    return render_template("index.html", message="Must be logged in to update a blog!")


if __name__ == "__main__":
    app.debug = True
    app.run()
