import os, io, secrets, sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, abort
from werkzeug.security import generate_password_hash, check_password_hash
import qrcode
from ai_summary import generate_medical_summary

app = Flask(__name__)
# Secure secret key handling
# In production the SECRET_KEY environment variable must be set.
# For local development you can use DEV_SECRET_KEY or a hard‑coded dev key.
if os.getenv("FLASK_ENV") == "development" or os.getenv("FLASK_DEBUG") == "1":
    # Development mode – allow a default dev key if not provided.
    app.secret_key = os.getenv("DEV_SECRET_KEY", "dev-secret-key")
else:
    secret = os.getenv("SECRET_KEY")
    if not secret:
        raise RuntimeError("SECRET_KEY environment variable is required in production. Set it before running the app.")
    app.secret_key = secret
DB_PATH = os.path.join(os.path.dirname(__file__), "med_emergency.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL, created_at TEXT NOT NULL
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER PRIMARY KEY,
            age TEXT DEFAULT '', blood_group TEXT DEFAULT '',
            allergies TEXT DEFAULT '', medicines TEXT DEFAULT '',
            history TEXT DEFAULT '', medicine_name TEXT DEFAULT '', medicine_dose TEXT DEFAULT '',
            medicine_frequency TEXT DEFAULT '', medicine_time TEXT DEFAULT '', emergency_name TEXT DEFAULT '',
            emergency_phone TEXT DEFAULT '', emergency_relation TEXT DEFAULT '',
            show_age INTEGER DEFAULT 1, show_blood_group INTEGER DEFAULT 1,
            show_allergies INTEGER DEFAULT 1, show_medicines INTEGER DEFAULT 1,
            show_history INTEGER DEFAULT 0, show_contact INTEGER DEFAULT 1,
            qr_token TEXT UNIQUE NOT NULL, updated_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )""")
        # Safe schema migration for databases created by an earlier version.
        existing = {row[1] for row in db.execute("PRAGMA table_info(profiles)").fetchall()}
        for column in ["medicine_name", "medicine_dose", "medicine_frequency", "medicine_time"]:
            if column not in existing:
                db.execute(f"ALTER TABLE profiles ADD COLUMN {column} TEXT DEFAULT ''")

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your name, a valid email and a password of at least 8 characters.", "danger")
            return render_template("register.html")
        try:
            with get_db() as db:
                cur = db.execute("INSERT INTO users(name,email,password_hash,created_at) VALUES(?,?,?,?)",
                    (name, email, generate_password_hash(password), datetime.utcnow().isoformat()))
                uid = cur.lastrowid
                db.execute("INSERT INTO profiles(user_id,qr_token,updated_at) VALUES(?,?,?)",
                    (uid, secrets.token_urlsafe(24), datetime.utcnow().isoformat()))
            session["user_id"] = uid
            session["name"] = name
            return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError:
            flash("This email is already registered.", "danger")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"], session["name"] = user["id"], user["name"]
            return redirect(url_for("dashboard"))
        flash("Incorrect email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
        profile = db.execute("SELECT * FROM profiles WHERE user_id=?", (session["user_id"],)).fetchone()
    return render_template("dashboard.html", user=user, p=profile)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        fields = {
            "age": request.form.get("age", "").strip(),
            "blood_group": request.form.get("blood_group", "").strip(),
            "allergies": request.form.get("allergies", "").strip(),
            "medicines": request.form.get("medicines", "").strip(),
            "history": request.form.get("history", "").strip(),
            "medicine_name": request.form.get("medicine_name", "").strip(),
            "medicine_dose": request.form.get("medicine_dose", "").strip(),
            "medicine_frequency": request.form.get("medicine_frequency", "").strip(),
            "medicine_time": request.form.get("medicine_time", "").strip(),
            "emergency_name": request.form.get("emergency_name", "").strip(),
            "emergency_phone": request.form.get("emergency_phone", "").strip(),
            "emergency_relation": request.form.get("emergency_relation", "").strip(),
        }
        flags = {k: 1 if request.form.get(k) == "on" else 0 for k in
                 ["show_age","show_blood_group","show_allergies","show_medicines","show_history","show_contact"]}
        with get_db() as db:
            db.execute("""UPDATE profiles SET age=?,blood_group=?,allergies=?,medicines=?,history=?,
                medicine_name=?,medicine_dose=?,medicine_frequency=?,medicine_time=?,
                emergency_name=?,emergency_phone=?,emergency_relation=?,
                show_age=?,show_blood_group=?,show_allergies=?,show_medicines=?,show_history=?,show_contact=?,
                updated_at=? WHERE user_id=?""",
                (*fields.values(), *flags.values(), datetime.utcnow().isoformat(), session["user_id"]))
        flash("Medical profile updated.", "success")
        return redirect(url_for("dashboard"))
    with get_db() as db:
        p = db.execute("SELECT * FROM profiles WHERE user_id=?", (session["user_id"],)).fetchone()
    return render_template("profile.html", p=p)

@app.route("/summary")
@login_required
def summary():
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
        if not user:
            flash("User not found. Please log in again.", "warning")
            return redirect(url_for("login"))
        p = db.execute("SELECT * FROM profiles WHERE user_id=?", (session["user_id"],)).fetchone()
        if not p:
            flash("Profile not found. Please create your profile.", "warning")
            return redirect(url_for("profile"))
    result = generate_medical_summary(user["name"], dict(p))
    updated = datetime.fromisoformat(p["updated_at"]).strftime("%d %b %Y, %I:%M %p")
    return render_template("summary.html", summary=result, p=p, updated=updated)

@app.route("/qr")
@login_required
def qr_code():
    with get_db() as db:
        p = db.execute("SELECT qr_token FROM profiles WHERE user_id=?", (session["user_id"],)).fetchone()
    public_url = url_for("emergency_view", token=p["qr_token"], _external=True)
    img = qrcode.make(public_url)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return send_file(buffer, mimetype="image/png", download_name="med-emergency-qr.png")

@app.route("/emergency/<token>")
def emergency_view(token):
    with get_db() as db:
        row = db.execute("""SELECT u.name,p.* FROM profiles p JOIN users u ON u.id=p.user_id
                            WHERE p.qr_token=?""", (token,)).fetchone()
    if not row:
        abort(404)
    p = dict(row)
    visible = {
        "Age": p["age"] if p["show_age"] else "",
        "Blood Group": p["blood_group"] if p["show_blood_group"] else "",
        "Drug Allergies": p["allergies"] if p["show_allergies"] else "",
        "Current Medicines": p["medicines"] if p["show_medicines"] else "",
        "Medical History": p["history"] if p["show_history"] else "",
    }
    contact = None
    if p["show_contact"] and (p["emergency_name"] or p["emergency_phone"]):
        contact = {"name":p["emergency_name"], "phone":p["emergency_phone"], "relation":p["emergency_relation"]}
    if p["show_medicines"] and p.get("medicine_name"):
        schedule = p["medicine_name"]
        if p.get("medicine_dose"): schedule += " · " + p["medicine_dose"]
        if p.get("medicine_frequency"): schedule += " · " + p["medicine_frequency"]
        if p.get("medicine_time"): schedule += " · " + p["medicine_time"]
        visible["Medicine Schedule"] = schedule
    summary = generate_medical_summary(p["name"], p, public=True)
    updated = datetime.fromisoformat(p["updated_at"]).strftime("%d %b %Y, %I:%M %p")
    return render_template("emergency.html", name=p["name"], details=visible, contact=contact,
                           updated=updated, summary=summary)

@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
