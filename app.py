from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import math

app = Flask(__name__)
app.secret_key = "secret123"


# -----------------------------
# Create Database Tables
# -----------------------------
def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # houses table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS houses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        price INTEGER,
        owner TEXT,
        phone TEXT,
        address TEXT,
        latitude REAL,
        longitude REAL
    )
    """)

    # users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


# -----------------------------
# Distance Calculation
# -----------------------------
def distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


# -----------------------------
# Signup
# -----------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        
        hashed = generate_password_hash(password)
        cur.execute("INSERT INTO users(username,password,role) VALUES(?,?,?)",
                    (username, hashed, role))

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("signup.html")


# -----------------------------
# Login
# -----------------------------
from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("SELECT password, role FROM users WHERE username=?", (username,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[0], password):
            role = user[1]
            session["user"] = username
            session["role"] = role

            if role == "owner":
                return redirect('/owner_dashboard')
            else:
                return redirect('/user_dashboard')
        else:
            return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')

# -----------------------------
# Logout
# -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# -----------------------------
# Get Location (USER)
# -----------------------------
@app.route('/get-location')
def get_location():
    if "user" not in session or session["role"] != "user":
        return redirect("/login")
    return render_template('get_location.html')


# -----------------------------
# Home Page
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# Show Nearby Houses (USER)
# -----------------------------
@app.route("/houses")
def houses():
    if "user" not in session or session["role"] != "user":
        return redirect("/login")

    lat = request.args.get("lat")
    lon = request.args.get("lon")
    if not lat or not lon:
        return redirect("/")

    lat = float(lat)
    lon = float(lon)
    bhk = request.args.get("bhk")
    max_price = request.args.get("price")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM houses")
    data = cur.fetchall()
    conn.close()

    result = []
    for h in data:
        if bhk and bhk != h[1]:
            continue
        if max_price and max_price.strip():
            if h[2] > int(max_price):
                continue
        d = distance(lat, lon, h[6], h[7])
        if d <= 20:
            result.append((h, d))

    result.sort(key=lambda x: x[1])
    return render_template("houses.html", houses=result, user_lat=lat, user_lon=lon)


# -----------------------------
# Add House (OWNER ONLY)
# -----------------------------
@app.route("/add_house", methods=["GET", "POST"])
def add_house():
    if "user" not in session or session["role"] != "owner":
        return redirect("/login")

    if request.method == "POST":
        type = request.form["type"]
        price = request.form["price"]
        owner = request.form["owner"]
        phone = request.form["phone"]
        address = request.form["address"]
        latitude = request.form["latitude"]
        longitude = request.form["longitude"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO houses(type,price,owner,phone,address,latitude,longitude) VALUES(?,?,?,?,?,?,?)",
            (type, price, owner, phone, address, latitude, longitude)
        )
        conn.commit()
        conn.close()

        return redirect("/owner_dashboard")


    return render_template("add_house.html")


# -----------------------------
# Owner Dashboard (OWNER ONLY)
# -----------------------------
@app.route("/owner_dashboard")
def owner_dashboard():
    if "user" not in session or session["role"] != "owner":
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM houses")
    houses = cur.fetchall()
    conn.close()

    return render_template("dashboard.html", houses=houses)

#user dashboard#
@app.route("/user_dashboard")
def user_dashboard():
    if "user" not in session or session["role"] != "user":
        return redirect("/login")
    return redirect("/get-location")


# -----------------------------
# Delete House (OWNER ONLY)
# -----------------------------
@app.route("/delete/<int:id>")
def delete(id):
    if "user" not in session or session["role"] != "owner":
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM houses WHERE id=?", (id,))
    conn.commit()
    conn.close()


    return redirect("/owner_dashboard")


# -----------------------------
# Add Sample Houses
# -----------------------------
@app.route("/add_sample")
def add_sample():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    sample_data = [
        ("1BHK",7000,"Mahesh","9876509876","Subedari, Warangal",17.9751,79.5902),
        ("2BHK",12000,"Suresh","9876512345","Kazipet, Warangal",17.9784,79.6062),
        ("1BHK",8000,"Ramesh","9876543210","Hanamkonda, Warangal",17.9689,79.5941),
        ("3BHK",20000,"Lakshmi","9876598765","Warangal City",17.9680,79.5930),
        ("2BHK",15000,"Anil","9876501122","Hunter Road, Warangal",17.9715,79.6020),
        ("1BHK",6000,"Kiran","9876502233","Naimnagar, Warangal",17.9725,79.5955),
        ("3BHK",22000,"Ravi","9876503344","KUC Road, Warangal",17.9830,79.5300),
        ("2BHK",13000,"Prasad","9876504455","Balasamudram, Warangal",17.9758,79.6012),
        ("1BHK",7500,"Venu","9876505566","Excise Colony, Warangal",17.9699,79.5999),
        ("2BHK",14000,"Srinu","9876506677","Kakatiya Colony, Warangal",17.9705,79.5970)
    ]

    for h in sample_data:
        cur.execute(
            "INSERT INTO houses(type,price,owner,phone,address,latitude,longitude) VALUES(?,?,?,?,?,?,?)",
            h
        )

    conn.commit()
    conn.close()

    return "✅ 10 Sample houses added!"


# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)