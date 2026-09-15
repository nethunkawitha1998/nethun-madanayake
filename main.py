"""
main.py
--------
Flask application entry point and configuration for the
"Impact of AI-Based Solutions on Incident Response Efficiency in SOC
Environments" research site.

Run locally:
    pip install -r requirements.txt
    python main.py

Then open http://127.0.0.1:5000 in a browser.
"""

import json
import os
import sqlite3
import uuid
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, send_from_directory, flash, g
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import analysis
import mitre

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
RESULTS_FOLDER = os.path.join(BASE_DIR, "uploads", "results")
DATABASE = os.path.join(BASE_DIR, "users.db")
ALLOWED_EXTENSIONS = {"csv"}

GOOGLE_FORM_URL = (
    "https://docs.google.com/forms/d/e/"
    "1FAIpQLSfSrEEgZFvEDY9pm6mpI5Saim4IU0-24xSkcU8sBl87AbG4ig/"
    "viewform?usp=sharing&ouid=114509313058798884619"
)

RESEARCHER = {
    "name": "Nethun Kawitha Madanayake",
    "role": "Senior Information Security Engineer",
    "affiliation": "SentryLabs Pvt. Ltd.",
    # Fill in the exact degree titles and awarding institutions here.
    "qualifications": [
        "MSc in Cybersecurity (in progress) — [University Name]",
        "[BSc / undergraduate degree — University Name]",
        "[Relevant industry certifications, e.g. CEH / CISSP / OSCP]",
    ],
    "linkedin": "https://www.linkedin.com/in/nethun-madanayake/",
    "email": "nethunkawitha5@gmail.com",
    "contact": "+94 76 329 3776 (Mobile & WhatsApp)",
    "photo": "nethun.jpg",
}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder=None, template_folder="templates")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-key-change-in-production")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB upload cap


# ---------------------------------------------------------------------------
# Database helpers (lightweight SQLite user store)
# ---------------------------------------------------------------------------
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DATABASE) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)
        db.commit()


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("sign_in"))
        return view_func(*args, **kwargs)
    return wrapped


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------------------------------------------------------------------
# Static-style asset routes (per required directory structure: styles/, images/)
# ---------------------------------------------------------------------------
@app.route("/styles/<path:filename>")
def styles(filename):
    return send_from_directory(os.path.join(BASE_DIR, "styles"), filename)


@app.route("/images/<path:filename>")
def images(filename):
    return send_from_directory(os.path.join(BASE_DIR, "images"), filename)


# ---------------------------------------------------------------------------
# Public routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template(
        "index.html",
        google_form_url=GOOGLE_FORM_URL,
        researcher=RESEARCHER,
        logged_in="user_id" in session,
    )


@app.route("/sign-up", methods=["GET", "POST"])
def sign_up():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not full_name or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("sign_up"))
        if password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("sign_up"))
        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return redirect(url_for("sign_up"))

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
                (full_name, email, generate_password_hash(password)),
            )
            db.commit()
        except sqlite3.IntegrityError:
            flash("An account with that email already exists.", "danger")
            return redirect(url_for("sign_up"))

        flash("Account created successfully. Please sign in.", "success")
        return redirect(url_for("sign_in"))

    return render_template("sign-up.html")


@app.route("/sign-in", methods=["GET", "POST"])
def sign_in():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("sign_in"))

        session["user_id"] = user["id"]
        session["full_name"] = user["full_name"]
        flash(f"Welcome back, {user['full_name']}!", "success")
        return redirect(url_for("analysis_page"))

    return render_template("sign-in.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Analysis workflow
# ---------------------------------------------------------------------------
@app.route("/analysis", methods=["GET", "POST"])
@login_required
def analysis_page():
    if request.method == "POST":
        if "csv_file" not in request.files:
            flash("No file selected.", "danger")
            return redirect(url_for("analysis_page"))

        file = request.files["csv_file"]
        if file.filename == "":
            flash("No file selected.", "danger")
            return redirect(url_for("analysis_page"))

        if not allowed_file(file.filename):
            flash("Please upload a .csv file.", "danger")
            return redirect(url_for("analysis_page"))

        filename = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
        file.save(filepath)

        try:
            results = analysis.run_full_analysis(filepath)
        except analysis.AnalysisError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("analysis_page"))
        finally:
            # remove the raw uploaded file; only derived, anonymised
            # composite results are retained for the results page
            if os.path.exists(filepath):
                os.remove(filepath)

        # persist the (already-aggregated, non-identifying) results to a
        # per-session JSON file rather than the cookie-based session, since
        # full result payloads can exceed typical cookie size limits
        result_id = uuid.uuid4().hex
        result_path = os.path.join(RESULTS_FOLDER, f"{result_id}.json")
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(results, f)
        session["result_id"] = result_id

        flash("Analysis complete.", "success")
        return redirect(url_for("results_page"))

    return render_template("analysis.html")


@app.route("/results")
@login_required
def results_page():
    result_id = session.get("result_id")
    if not result_id:
        flash("No analysis results yet — please upload a dataset first.", "warning")
        return redirect(url_for("analysis_page"))

    result_path = os.path.join(RESULTS_FOLDER, f"{result_id}.json")
    if not os.path.exists(result_path):
        flash("Your analysis results have expired — please upload the dataset again.", "warning")
        return redirect(url_for("analysis_page"))

    with open(result_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    recommendations = mitre.generate_recommendations(results.get("construct_means", {}))
    countermeasures = mitre.get_countermeasures()
    future_directions = mitre.get_future_directions()

    return render_template(
        "results.html",
        results=results,
        recommendations=recommendations,
        countermeasures=countermeasures,
        future_directions=future_directions,
        mitre_url=mitre.MITRE_ATTACK_URL,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)
else:
    # Ensure DB exists even when imported by a WSGI server (e.g. gunicorn)
    init_db()
