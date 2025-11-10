from flask import Flask, redirect, request, render_template, send_file
import sqlite3, datetime, os
import pandas as pd
import folium
import io

app = Flask(__name__)

DB = "database.db"

# Création de la base si elle n'existe pas
if not os.path.exists(DB):
    conn = sqlite3.connect(DB)
    conn.execute("""
    CREATE TABLE scans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        qr_id TEXT,
        city TEXT,
        date TEXT
    )
    """)
    conn.close()

# Route pour tracker le QR
@app.route("/qr/<qr_id>")
def track_qr(qr_id):
    # On prend le nom du QR comme ville
    city = qr_id

    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT INTO scans (qr_id, city, date) VALUES (?, ?, ?)",
        (qr_id, city, datetime.datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    # Redirige vers ton Spotify
    return redirect("https://open.spotify.com/intl-fr/artist/7ezsPfUbut94F7g4dXi5Fl?si=XdamSx0dT12HMHhJbb3e2g")

# Dashboard
@app.route("/")
def dashboard():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT city FROM scans")
    rows = cursor.fetchall()
    conn.close()

    total = len(rows)

    # Compte le nombre de scans par ville
    city_counts = {}
    for r in rows:
        city_name = r[0] or "Ville inconnue"
        city_counts[city_name] = city_counts.get(city_name, 0) + 1

    # Tri par nombre de scans décroissant
    city_counts = dict(sorted(city_counts.items(), key=lambda x: x[1], reverse=True))

    return render_template("dashboard.html", total=total, city_counts=city_counts)

# Télécharger Excel
@app.route("/download")
def download_excel():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT qr_id, city, date FROM scans ORDER BY date DESC", conn)
    conn.close()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Scans")
    output.seek(0)
    return send_file(output, download_name="qr_scans.xlsx", as_attachment=True)

# Carte des scans
@app.route("/map")
def map_view():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT city FROM scans")
    rows = cursor.fetchall()
    conn.close()

    # Carte centrée sur la France
    m = folium.Map(location=[46.6, 2.5], zoom_start=5)

    # Coordonnées approximatives pour certaines villes
    city_coords = {
        "marseille1": [43.2965, 5.3698],
        "paris1": [48.8566, 2.3522],
        "lyon1": [45.7640, 4.8357],
        "nice1": [43.7102, 7.2620],
        # Ajouter d'autres villes si nécessaire
    }

    for row in rows:
        city = row[0]
        if city in city_coords:
            folium.CircleMarker(
                location=city_coords[city],
                radius=6,
                popup=city,
                color="blue",
                fill=True,
                fill_color="cyan"
            ).add_to(m)

    # Sauvegarde dans un fichier HTML
    map_file = "templates/map.html"
    m.save(map_file)
    return render_template("map.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
