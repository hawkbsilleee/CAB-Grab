from flask import Flask, request, render_template_string
import sqlite3
import smtplib
from email.mime.text import MIMEText
import time
import threading
from backgroundscript import get_open_seats  # import your seat checker

app = Flask(__name__)
DB = "subscriptions.db"


# --- DB Setup ---
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        crn TEXT NOT NULL
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
        for crn in crns:
            c.execute("INSERT INTO subscriptions (email, crn) VALUES (?, ?)", (email.strip(), crn.strip()))
        conn.commit()
        conn.close()
        return "✅ You're subscribed!"
    
    return render_template_string("""
        <h2>Brown Course Tracker</h2>
        <form method="post">
            Email: <input type="email" name="email" required><br>
            CRNs (comma separated): <input type="text" name="crns" required><br>
            <button type="submit">Track</button>
        </form>
    """)


# --- Email Helper ---
def send_email(to_email, crn, seats):
    msg = MIMEText(f"A seat just opened for CRN {crn}! with {seats} seats available.")
    msg["Subject"] = f"Brown Course Alert: {crn}"
    msg["From"] = "your_email@gmail.com"
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login("dhruvjain2905@gmail.com", "biqr pgod hozm ctgk")  # use app password!
        server.sendmail("dhruvjain2905@gmail.com", [to_email], msg.as_string())


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
                seats = get_open_seats(crn)
                #if isinstance(seats, int) and seats > 0:

                send_email(email, crn, seats)
                print(f"Sent alert to {email} for CRN {crn}")

            except Exception as e:
                print(f"Error checking {crn}: {e}")

        time.sleep(30)  # check every 5 minutes


# --- Start Poller in Background Thread ---
threading.Thread(target=poll_loop, daemon=True).start()


if __name__ == "__main__":
    app.run(debug=True)