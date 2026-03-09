from flask import Flask, render_template, request, redirect
import sqlite3
import math

app = Flask(__name__)


# -----------------------------
# Create Database Table
# -----------------------------
def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

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
# Home Page
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# Show Nearby Houses
# -----------------------------
@app.route("/houses")
def houses():

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

    result = []

    for h in data:

        if bhk and bhk != h[1]:
            continue

        if max_price and max_price.strip():
            if h[2] > int(max_price):
                continue

        d = distance(lat, lon, h[6], h[7])

        # Only show houses within 20 km
        if d <= 20:
            result.append((h, d))

    result.sort(key=lambda x: x[1])

    conn.close()

    return render_template(
        "houses.html",
        houses=result,
        user_lat=lat,
        user_lon=lon,
        selected_bhk=bhk,
        selected_price=max_price
    )


# -----------------------------
# Add House
# -----------------------------
@app.route("/add_house", methods=["GET", "POST"])
def add_house():

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

        return redirect("/")

    return render_template("add_house.html")


# -----------------------------
# Owner Dashboard
# -----------------------------
@app.route("/dashboard")
def dashboard():

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM houses")
    houses = cur.fetchall()

    conn.close()

    return render_template("dashboard.html", houses=houses)


# -----------------------------
# Delete House
# -----------------------------
@app.route("/delete/<int:id>")
def delete(id):

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("DELETE FROM houses WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# -----------------------------
# Add Sample Houses (for demo)
# -----------------------------
@app.route("/add_sample")
def add_sample():

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    sample_data = [

        ("1BHK",7000,"Mahesh","9876509876","Subedari",17.9751,79.5902),
        ("2BHK",12000,"Suresh","9876512345","Kazipet",17.9784,79.6062),
        ("1BHK",8000,"Ramesh","9876543210","Hanamkonda",17.9689,79.5941),
        ("3BHK",20000,"Lakshmi","9876598765","Warangal",17.9680,79.5930)

    ]

    for h in sample_data:
        cur.execute(
            "INSERT INTO houses(type,price,owner,phone,address,latitude,longitude) VALUES(?,?,?,?,?,?,?)",
            h
        )

    conn.commit()
    conn.close()

    return "Sample houses added successfully!"


# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)