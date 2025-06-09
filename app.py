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
from flask_socketio import SocketIO
from datetime import datetime
import pytz

load_dotenv()
import os
print(os.path.abspath("incidents.db"))

# --- App setup ---
app = Flask(__name__)
app.secret_key = 'emergencyMangntsolutionus'
socketio = SocketIO(app, cors_allowed_origins="*")

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

@socketio.on('connect')
def handle_connect():
    print('Client connected')

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
    if 'user_name' not in session:
        return redirect(url_for('signin'))  # Redirect to login if not authenticated

    db = get_db()

    total = db.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
    recent = db.execute("SELECT * FROM incidents ORDER BY created_at DESC LIMIT 10").fetchall()

    # Eastern timezone formatting
    eastern = pytz.timezone('America/New_York')
    now = datetime.now(eastern)
    day = now.day
    suffix = 'th' if 11 <= day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    formatted_date = f"{day}<sup>{suffix}</sup> {now.strftime('%B %Y, %A, %I:%M %p')}"

    # Weather API
    city = "Washington"
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

    return render_template(
        "dashboard.html",
        total=total,
        date_now=formatted_date,
        recent=recent,
        weather=weather
    )

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
    status_rows = db.execute("SELECT status, COUNT(*) as count FROM incidents GROUP BY status").fetchall()
    city_rows = db.execute("SELECT location, COUNT(*) as count FROM incidents GROUP BY location").fetchall()

    all_locations = db.execute("SELECT id, name, category, location, latitude, longitude FROM incidents WHERE latitude IS NOT NULL AND longitude IS NOT NULL").fetchall()
    latest_incident = db.execute("SELECT id FROM incidents ORDER BY created_at DESC LIMIT 1").fetchone()
    latest_id = latest_incident["id"] if latest_incident else None

    return jsonify({
        'category_data': {row["category"]: row["count"] for row in category_rows},
        'date_data': {row["date"]: row["count"] for row in date_rows},
        'status_data': {row["status"]: row["count"] for row in status_rows},
        'city_data': {row["location"]: row["count"] for row in city_rows},
        'locations': [dict(row) for row in all_locations],
        'latest_id': latest_id
    })

@app.route('/thank-you')
def thank_you():
    return render_template('thank_you.html')

@app.route('/api/weather')
def get_weather():
    city = "Washington"
    api_key = os.getenv("WEATHER_API_KEY")
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'
    response = requests.get(url)
    return jsonify(response.json())

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        user = db.execute("SELECT * FROM admin_users WHERE username = ? AND password = ?", (username, password)).fetchone()

        if user:
            session['user_name'] = username
            return redirect(url_for('dashboard'))  # send to dashboard only if authenticated
        else:
            error = 'Invalid username or password'

    return render_template('login.html', error=error)

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
   

    db = get_db()

    # Fetch all complaints
    complaints = db.execute("SELECT * FROM incidents ORDER BY created_at DESC").fetchall()
    total = len(complaints)

    # Fetch recent notifications (limit 5)
    notifications = db.execute(
        "SELECT * FROM notifications ORDER BY created_at DESC LIMIT 5"
    ).fetchall()

    # Define Eastern Time Zone (Laurel, MD is in ET)
    eastern = pytz.timezone('America/New_York')
    now = datetime.now(eastern)

    # Add correct suffix for the day
    day = now.day
    suffix = 'th' if 11 <= day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')

    # Format with superscript suffix
    formatted_date = f"{day}<sup>{suffix}</sup> {now.strftime('%B %Y, %A, %I:%M %p')}"
    # Fetch weather data
    city = "Washington"
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

    return render_template(
        "user_dashboard.html",
        complaints=complaints,
        total=total,
        notifications=notifications,
        weather=weather,
        date_now=formatted_date, 
    )



#flood dashboard
@app.route('/flood', methods=['GET'])
def show_flood_dashboard():
    return render_template('flood.html')

from flask import jsonify

@app.route("/api/flood-data")
def get_flood_data():
    db = get_db()
    rows = db.execute(
        "SELECT name, location, severity, description, created_at, status FROM incidents WHERE category = 'Flood' ORDER BY created_at DESC"
    ).fetchall()

    incidents = [dict(row) for row in rows]
    return jsonify({"incidents": incidents})


# Handle real-time flood report submission
@app.route('/report_flood', methods=['POST'])
def report_flood():
    data = request.json
    data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['category'] = 'Flood'

    try:
        db = get_db()
        db.execute(
            '''INSERT INTO complaints (name, phone, category, severity, location, description, created_at, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (data['name'], data['phone'], data['category'], data['severity'],
             data['location'], data['description'], data['created_at'], data['status'])
        )
        db.commit()
    except Exception as db_error:
        print("Database insert failed in /report_flood:", db_error)
        return jsonify({'status': 'error', 'message': 'Database error occurred.'}), 500

    return jsonify({'status': 'success'}), 200




#fire dashboard
@app.route('/fire', methods=['GET'])
def show_fire_dashboard():
    return render_template('fire.html')

from flask import jsonify

@app.route("/api/fire-data")
def get_fire_data():
    db = get_db()
    rows = db.execute(
        "SELECT name, location, severity, description, created_at, status FROM incidents WHERE category = 'Fire' ORDER BY created_at DESC"
    ).fetchall()

    incidents = [dict(row) for row in rows]
    return jsonify({"incidents": incidents})


# Handle real-time fire report submission
@app.route('/report_fire', methods=['POST'])
def report_fire():
    data = request.json
    data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['category'] = 'Fire'

    try:
        db = get_db()
        db.execute(
            '''INSERT INTO complaints (name, phone, category, severity, location, description, created_at, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (data['name'], data['phone'], data['category'], data['severity'],
             data['location'], data['description'], data['created_at'], data['status'])
        )
        db.commit()
    except Exception as db_error:
        print("Database insert failed in /report_fire:", db_error)
        return jsonify({'status': 'error', 'message': 'Database error occurred.'}), 500

    return jsonify({'status': 'success'}), 200


#water dashboard
@app.route('/water', methods=['GET'])
def show_water_dashboard():
    return render_template('water.html')

from flask import jsonify

@app.route("/api/water-data")
def get_water_data():
    db = get_db()
    rows = db.execute(
        "SELECT name, location, severity, description, created_at, status FROM incidents WHERE category = 'Water' ORDER BY created_at DESC"
    ).fetchall()

    incidents = [dict(row) for row in rows]
    return jsonify({"incidents": incidents})


# Handle real-time water report submission
@app.route('/report_water', methods=['POST'])
def report_water():
    data = request.json
    data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['category'] = 'water'

    try:
        db = get_db()
        db.execute(
            '''INSERT INTO complaints (name, phone, category, severity, location, description, created_at, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (data['name'], data['phone'], data['category'], data['severity'],
             data['location'], data['description'], data['created_at'], data['status'])
        )
        db.commit()
    except Exception as db_error:
        print("Database insert failed in /report_water:", db_error)
        return jsonify({'status': 'error', 'message': 'Database error occurred.'}), 500

    return jsonify({'status': 'success'}), 200

#sewer dashboard
@app.route('/sewer', methods=['GET'])
def show_sewer_dashboard():
    return render_template('sewer.html')

from flask import jsonify

@app.route("/api/sewer-data")
def get_sewer_data():
    db = get_db()
    rows = db.execute(
        "SELECT name, location, severity, description, created_at, status FROM incidents WHERE category = 'Sewer' ORDER BY created_at DESC"
    ).fetchall()

    incidents = [dict(row) for row in rows]
    return jsonify({"incidents": incidents})


# Handle real-time sewer report submission
@app.route('/report_sewer', methods=['POST'])
def report_sewer():
    data = request.json
    data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['category'] = 'Sewer'

    try:
        db = get_db()
        db.execute(
            '''INSERT INTO complaints (name, phone, category, severity, location, description, created_at, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (data['name'], data['phone'], data['category'], data['severity'],
             data['location'], data['description'], data['created_at'], data['status'])
        )
        db.commit()
    except Exception as db_error:
        print("Database insert failed in /report_sewer:", db_error)
        return jsonify({'status': 'error', 'message': 'Database error occurred.'}), 500

    return jsonify({'status': 'success'}), 200


@app.route("/admin_notify")
def admin_notify():
    return render_template("admin_notify.html")


@app.route('/send_notification', methods=['POST'])
def send_notification():
    title = request.form['title']
    message = request.form['message']
    category = request.form['category']
    area = request.form['area']

    image_file = request.files.get('image')
    image_filename = None

    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file = request.files.get('photo')
        image_filename = filename  # Save this in your DB if needed

    # Save the notification to the database (including image_filename if used)

    flash('Notification sent successfully!')
    return redirect(url_for('your_notify_route'))  # Replace with actual route name

@app.route("/incident/<int:id>")
def view_incident(id):
    db = get_db()
    incident = db.execute("SELECT * FROM incidents WHERE id = ?", (id,)).fetchone()
    return render_template("incident_detail.html", incident=incident)

@app.route("/incident/<int:id>/update_status", methods=["POST"])
def update_status(id):
    new_status = request.form["status"]
    db = get_db()
    db.execute("UPDATE incidents SET status = ? WHERE id = ?", (new_status, id))
    db.commit()
    return redirect(url_for("view_incident", id=id))



if __name__ == "__main__":
    socketio.run(app, debug=True)

