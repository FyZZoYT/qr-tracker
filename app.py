from flask import Flask, redirect, request, render_template
import sqlite3, datetime, requests, os

app = Flask(__name__)

DB = "database.db"

# Création de la base si elle n'existe pas
if not os.path.exists(DB):
    conn = sqlite3.connect(DB)
    conn.execute("""
    CREATE TABLE scans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        qr_id TEXT,
        ip TEXT,
        country TEXT,
        city TEXT,
        date TEXT
    )
    """)
    conn.close()

def get_geo(ip):
    try:
        r = requests.get(f"https://ipapi.co/{ip}/json/").json()
        return r.get("country_name", "Inconnu"), r.get("city", "Inconnue")
    except:
        return "Inconnu", "Inconnue"

@app.route("/qr/<qr_id>")
def track_qr(qr_id):
    ip = request.remote_addr
    country, city = get_geo(ip)
    conn = sqlite3.connect(DB)
    conn.execute("INSERT INTO scans (qr_id, ip, country, city, date) VALUES (?, ?, ?, ?, ?)",
                 (qr_id, ip, country, city, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()
    # Redirige vers ton lien Spotify
    return redirect("https://open.spotify.com/intl-fr/artist/7ezsPfUbut94F7g4dXi5Fl?si=XdamSx0dT12HMHhJbb3e2g")

@app.route("/")
def dashboard():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT qr_id, country, city, date FROM scans ORDER BY date DESC")
    scans = cursor.fetchall()
    conn.close()
    total = len(scans)
    return render_template("dashboard.html", scans=scans, total=total)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
