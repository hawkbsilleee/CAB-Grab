from flask import Flask, request, render_template_string, render_template
import sqlite3
import threading
import time
from api_interface import get_course_info
from notifier import send_email

app = Flask(__name__, template_folder="templates")
DB = "subscriptions.db"

# --- DB Setup ---
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        crn TEXT NOT NULL,
        notified INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()

init_db()

# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        email = request.form["email"]
        crns = request.form["crns"].split(",")
        
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        
        # Insert each CRN for the email
        for crn in crns:
            crn = crn.strip()
            if crn:  # Only insert if CRN is not empty after stripping
                c.execute("INSERT INTO subscriptions (email, crn) VALUES (?, ?)", (email.strip(), crn))
        
        conn.commit()
        conn.close()
        
        # Flash a success message
        flash(f"✅ You're now tracking {len([c.strip() for c in crns if c.strip()])} course(s)!", "success")
        return redirect(url_for('index'))
    
    # GET request - fetch and display existing subscriptions
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # Fetch all subscriptions with basic info
    # Adjust this query based on your actual table structure
    c.execute("SELECT email, crn, datetime('now') FROM subscriptions ORDER BY rowid DESC")
    subscriptions = c.fetchall()
    
    conn.close()
    
    return render_template('index.html', subscriptions=subscriptions)

# --- Background Poller ---
def poll_loop():
    while True:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT email, crn FROM subscriptions")
        subs = c.fetchall()
        conn.close()

        for email, crn in subs:
            try:
                info = get_course_info(crn)
                seats = info["seats_available"]

                if seats > 0:  # only notify if seats are open
                    send_email(crn, email)
                    print(f"📧 Sent alert to {email} for CRN {crn} ({seats} seats open)")
            except Exception as e:
                print(f"❌ Error checking {crn}: {e}")

        time.sleep(60)  # poll every 60s (adjust if needed)

# --- Start poller in background ---
threading.Thread(target=poll_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(debug=True)