
# from flask import Flask, render_template, request, redirect, url_for, g, jsonify
# import sqlite3
# import os
# from werkzeug.utils import secure_filename
# from datetime import datetime
# import json
# from geopy.geocoders import Nominatim
# from dotenv import load_dotenv
# load_dotenv()
# from flask import session
# from werkzeug.security import generate_password_hash, check_password_hash

# print("✅ Debug: WEATHER_API_KEY =", os.getenv("WEATHER_API_KEY"))

# app = Flask(__name__)
# from flask import Flask, render_template, request, redirect, url_for, g, session, flash


# app.secret_key = 'emergencyMangntsolutionus' 


# # --- Config for uploads ---
# UPLOAD_FOLDER = 'uploads'
# ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# # --- Database connection ---
# DATABASE = 'incidents.db'


# def get_db():
#     if 'db' not in g:
#         g.db = sqlite3.connect(DATABASE)
#         g.db.row_factory = sqlite3.Row
#     return g.db

# import sqlite3

# def get_db_connection():
#     conn = sqlite3.connect('usersDetails.db')  # Same DB file as above
#     conn.row_factory = sqlite3.Row
#     return conn

# @app.teardown_appcontext
# def close_db(e=None):
#     db = g.pop('db', None)
#     if db is not None:
#         db.close()


# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# # --- Home Route ---
# @app.route("/")
# def home():
#     return render_template("home.html")


# # --- Admin Button Redirects to Dashboard Directly ---
# @app.route("/admin")
# def admin():
#     return redirect(url_for("dashboard"))


# # --- Incident Submission ---
# @app.route("/submit", methods=["POST"])
# def submit():
#     name = request.form['name']
#     phone = request.form['phone']
#     category = request.form['category']
#     severity = request.form['severity']
#     description = request.form.get('description', '')
#     location = request.form.get('location', '')

#     # Handle photo upload (optional)
#     photo = request.files.get('photo')
#     photo_path = ''
#     if photo and allowed_file(photo.filename):
#         filename = secure_filename(photo.filename)
#         photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         photo.save(photo_path)

#     # Optional geolocation (but non-blocking)
#     latitude = None
#     longitude = None
#     if location:
#         try:
#             geolocator = Nominatim(user_agent="incident_app")
#             loc = geolocator.geocode(location, timeout=10)
#             if loc:
#                 latitude = loc.latitude
#                 longitude = loc.longitude
#         except Exception as geo_error:
#             print("Geolocation failed:", geo_error)

#     try:
#         db = get_db()
#         db.execute(
#             '''INSERT INTO incidents (name, phone, category, severity, description, location, photo_path, latitude, longitude, created_at)
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
#             (name, phone, category, severity, description, location, photo_path, latitude, longitude, datetime.now())
#         )
#         db.commit()
#     except Exception as db_error:
#         print("Database insert failed:", db_error)

#     return redirect(url_for("thank_you"))


# # --- Show Complaint Form ---
# @app.route("/form")
# def form():
#     return render_template("form.html")


# # --- Admin Dashboard ---
# @app.route("/dashboard")
# def dashboard():
#     db = get_db()

#     total = db.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]

#     category_rows = db.execute("SELECT category, COUNT(*) as count FROM incidents GROUP BY category").fetchall()
#     category_data = {row["category"]: row["count"] for row in category_rows}

#     date_rows = db.execute("SELECT DATE(created_at) as date, COUNT(*) as count FROM incidents GROUP BY DATE(created_at)").fetchall()
#     date_data = {row["date"]: row["count"] for row in date_rows}

#     recent = db.execute("SELECT * FROM incidents ORDER BY created_at DESC LIMIT 5").fetchall()

#     all_locations = db.execute("""
#         SELECT id, name, category, location, latitude, longitude 
#         FROM incidents 
#         WHERE latitude IS NOT NULL AND longitude IS NOT NULL
#     """).fetchall()

#     latest_incident = db.execute("SELECT id FROM incidents ORDER BY created_at DESC LIMIT 1").fetchone()
#     latest_id = latest_incident["id"] if latest_incident else None

#         # 🌤️ Get weather
#     import requests, os
#     city = "Mumbai"
#     api_key = os.getenv("WEATHER_API_KEY")

#     print("Loaded API key:", api_key)  # ← 🔍 Debug print

#     weather = {}
#     try:
#         res = requests.get(
#             f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
#         )
#         print("Weather API response:", res.status_code, res.text)  # ← 🔍 Debug API response
#         if res.status_code == 200:
#             data = res.json()
#             weather = {
#                 "temp": data["main"]["temp"],
#                 "desc": data["weather"][0]["description"].title(),
#                 "city": city,
#             }
#     except Exception as e:
#         print("Weather error:", e)

#     return render_template("dashboard.html",
#                            total=total,
#                            recent=recent,
#                            category_data=json.dumps(category_data),
#                            date_data=json.dumps(date_data),
#                            locations=json.dumps([dict(row) for row in all_locations]),
#                            latest_id=latest_id,
#                            weather=weather)

# # --- Maps Route ---
# @app.route('/maps')
# def maps():
#     db = get_db()
#     locations = db.execute("""
#         SELECT id, name, category, location, latitude, longitude
#         FROM incidents
#         WHERE latitude IS NOT NULL AND longitude IS NOT NULL
#     """).fetchall()

#     locations_json = json.dumps([dict(row) for row in locations])

#     return render_template('maps.html', locations_json=locations_json)


# @app.route('/favicon.ico')
# def favicon():
#     return redirect(url_for('static', filename='favicon.ico'))


# # --- API endpoint to provide dashboard data ---
# @app.route("/api/dashboard-data")
# def dashboard_data():
#     db = get_db()

#     category_rows = db.execute("SELECT category, COUNT(*) as count FROM incidents GROUP BY category").fetchall()
#     category_data = {row["category"]: row["count"] for row in category_rows}

#     date_rows = db.execute("SELECT DATE(created_at) as date, COUNT(*) as count FROM incidents GROUP BY DATE(created_at)").fetchall()
#     date_data = {row["date"]: row["count"] for row in date_rows}

#     all_locations = db.execute("""
#         SELECT id, name, category, location, latitude, longitude 
#         FROM incidents 
#         WHERE latitude IS NOT NULL AND longitude IS NOT NULL
#     """).fetchall()

#     latest_incident = db.execute("SELECT id FROM incidents ORDER BY created_at DESC LIMIT 1").fetchone()
#     latest_id = latest_incident["id"] if latest_incident else None

#     return jsonify({
#         'category_data': category_data,
#         'date_data': date_data,
#         'locations': [dict(row) for row in all_locations],
#         'latest_id': latest_id
#     })


# # --- Thank You Page ---
# @app.route('/thank-you')
# def thank_you():
#     return render_template('thank_you.html')

# @app.route('/api/weather')
# def get_weather():
#     import requests
#     import os  # ← make sure this is at the top of your file too
#     city = "Mumbai"
#     api_key = os.getenv("WEATHER_API_KEY")
    
#     url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'
    
#     response = requests.get(url)
#     data = response.json()

#     return jsonify(data)

# # --- Sign Up Route ---
# @app.route("/signin", methods=["GET", "POST"])
# def signin():
#     db = get_db()
#     if request.method == "POST":
#         email = request.form["email"]
#         user = db.execute(
#             "SELECT * FROM usersDetails WHERE email = ?", (email,)
#         ).fetchone()

#         if user:
#             session["user_name"] = user["name"]
#             session["user_email"] = user["email"]
#             return redirect(url_for("user_dashboard"))
#         else:
#             flash("Invalid email. Please try again.")
#             return render_template("signin.html")

#     return render_template("signin.html")

# # --- Login Route ---
# from werkzeug.security import generate_password_hash

# @app.route("/signup", methods=["GET", "POST"])
# def signup():
#     conn = get_db_connection()
#     if request.method == "POST":
#         name = request.form["name"]
#         email = request.form["email"]
#         username = request.form["username"]
#         password = request.form["password"]

#         try:
#             conn.execute(
#                 "INSERT INTO usersDetails (name, email, username, password) VALUES (?, ?, ?, ?)",
#                 (name, email, username, password)
#             )
#             conn.commit()

#             # Store user info in session
#             session["user_name"] = name
#             session["user_email"] = email

#             return redirect(url_for("user_dashboard"))
#         except sqlite3.IntegrityError:
#             flash("Email or Username already exists.")
#             return render_template("signup.html")

#     return render_template("signup.html")


# # --- Logout Route ---
# @app.route('/logout')
# def logout():
#     session.clear()
#     return redirect(url_for('home'))

# # --- Updated User Dashboard with Auth Check ---
# @app.route("/user-dashboard")
# def user_dashboard():
#     if "user_name" not in session:
#         return redirect(url_for("signin"))
#     return render_template("user_dashboard.html")


# if __name__ == "__main__":
#     app.run(debug=True)



from flask import Flask, render_template, request, redirect, url_for, g, session, flash, jsonify
import sqlite3
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
import requests

load_dotenv()
import os
print(os.path.abspath("incidents.db"))

# --- App setup ---
app = Flask(__name__)
app.secret_key = 'emergencyMangntsolutionus'

# --- Config for uploads ---
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Database setup ---
INCIDENT_DB = 'incidents.db'
USER_DB = 'usersDetails.db'

# --- Helper functions ---
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(INCIDENT_DB)
        g.db.row_factory = sqlite3.Row
    return g.db

def get_user_db():
    if 'user_db' not in g:
        g.user_db = sqlite3.connect(USER_DB)
        g.user_db.row_factory = sqlite3.Row
    return g.user_db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db:
        db.close()
    user_db = g.pop('user_db', None)
    if user_db:
        user_db.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Routes ---
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/admin")
def admin():
    return redirect(url_for("dashboard"))

@app.route("/form")
def form():
    return render_template("form.html")

@app.route("/submit", methods=["POST"])
def submit():
    name = request.form['name']
    phone = request.form['phone']
    category = request.form['category']
    severity = request.form['severity']
    description = request.form.get('description', '')
    location = request.form.get('location', '')

    photo = request.files.get('photo')
    photo_path = ''
    if photo and allowed_file(photo.filename):
        filename = secure_filename(photo.filename)
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo.save(photo_path)

    latitude = longitude = None
    if location:
        try:
            geolocator = Nominatim(user_agent="incident_app")
            loc = geolocator.geocode(location, timeout=10)
            if loc:
                latitude, longitude = loc.latitude, loc.longitude
        except Exception as geo_error:
            print("Geolocation failed:", geo_error)

    try:
        db = get_db()
        db.execute(
            '''INSERT INTO incidents (name, phone, category, severity, description, location, photo_path, latitude, longitude, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (name, phone, category, severity, description, location, photo_path, latitude, longitude, datetime.now())
        )
        db.commit()
    except Exception as db_error:
        print("Database insert failed:", db_error)

    return redirect(url_for("thank_you"))

@app.route("/dashboard")
def dashboard():
    db = get_db()

    total = db.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
    category_rows = db.execute("SELECT category, COUNT(*) as count FROM incidents GROUP BY category").fetchall()
    date_rows = db.execute("SELECT DATE(created_at) as date, COUNT(*) as count FROM incidents GROUP BY DATE(created_at)").fetchall()
    recent = db.execute("SELECT * FROM incidents ORDER BY created_at DESC LIMIT 5").fetchall()
    all_locations = db.execute("""SELECT id, name, category, location, latitude, longitude 
                                  FROM incidents WHERE latitude IS NOT NULL AND longitude IS NOT NULL""").fetchall()
    latest_incident = db.execute("SELECT id FROM incidents ORDER BY created_at DESC LIMIT 1").fetchone()
    latest_id = latest_incident["id"] if latest_incident else None

    # Weather API
    city = "Mumbai"
    api_key = os.getenv("WEATHER_API_KEY")
    weather = {}
    try:
        res = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric")
        if res.status_code == 200:
            data = res.json()
            weather = {
                "temp": data["main"]["temp"],
                "desc": data["weather"][0]["description"].title(),
                "city": city,
            }
    except Exception as e:
        print("Weather error:", e)

    return render_template("dashboard.html",
                           total=total,
                           recent=recent,
                           category_data=json.dumps({row["category"]: row["count"] for row in category_rows}),
                           date_data=json.dumps({row["date"]: row["count"] for row in date_rows}),
                           locations=json.dumps([dict(row) for row in all_locations]),
                           latest_id=latest_id,
                           weather=weather)

@app.route("/maps")
def maps():
    db = get_db()
    locations = db.execute("SELECT id, name, category, location, latitude, longitude FROM incidents WHERE latitude IS NOT NULL AND longitude IS NOT NULL").fetchall()
    return render_template('maps.html', locations_json=json.dumps([dict(row) for row in locations]))

@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))

@app.route("/api/dashboard-data")
def dashboard_data():
    db = get_db()
    category_rows = db.execute("SELECT category, COUNT(*) as count FROM incidents GROUP BY category").fetchall()
    date_rows = db.execute("SELECT DATE(created_at) as date, COUNT(*) as count FROM incidents GROUP BY DATE(created_at)").fetchall()
    all_locations = db.execute("SELECT id, name, category, location, latitude, longitude FROM incidents WHERE latitude IS NOT NULL AND longitude IS NOT NULL").fetchall()
    latest_incident = db.execute("SELECT id FROM incidents ORDER BY created_at DESC LIMIT 1").fetchone()
    latest_id = latest_incident["id"] if latest_incident else None

    return jsonify({
        'category_data': {row["category"]: row["count"] for row in category_rows},
        'date_data': {row["date"]: row["count"] for row in date_rows},
        'locations': [dict(row) for row in all_locations],
        'latest_id': latest_id
    })

@app.route('/thank-you')
def thank_you():
    return render_template('thank_you.html')

@app.route('/api/weather')
def get_weather():
    city = "Mumbai"
    api_key = os.getenv("WEATHER_API_KEY")
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'
    response = requests.get(url)
    return jsonify(response.json())

@app.route("/signin", methods=["GET", "POST"])
def signin():
    user_db = get_user_db()
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = user_db.execute("SELECT * FROM usersDetails WHERE email = ?", (email,)).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            return redirect(url_for("user_dashboard"))
        else:
            flash("Invalid credentials.")
            return render_template("signin.html")
    return render_template("signin.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    user_db = get_user_db()
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]

        hashed_pw = generate_password_hash(password)
        try:
            user_db.execute(
                "INSERT INTO usersDetails (name, email, username, password) VALUES (?, ?, ?, ?)",
                (name, email, username, hashed_pw)
            )
            user_db.commit()
            session["user_name"] = name
            session["user_email"] = email
            return redirect(url_for("user_dashboard"))
        except sqlite3.IntegrityError:
            flash("Email or Username already exists.")
            return render_template("signup.html")
    return render_template("signup.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/user-dashboard')
def user_dashboard():
    # Fetch weather data (same as admin dashboard)
    city = "Mumbai"
    api_key = os.getenv("WEATHER_API_KEY")
    weather = {}
    try:
        res = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric")
        if res.status_code == 200:
            data = res.json()
            weather = {
                "temp": data["main"]["temp"],
                "desc": data["weather"][0]["description"].title(),
                "city": city,
            }
    except Exception as e:
        print("Weather error:", e)

    # Fetch all complaints
    db = get_db()
    complaints = db.execute("SELECT * FROM incidents ORDER BY created_at DESC").fetchall()
    total = len(complaints)

    return render_template(
        'user_dashboard.html',
        weather=weather,
        complaints=complaints,
        total=total
    )

if __name__ == "__main__":
    app.run(debug=True)
