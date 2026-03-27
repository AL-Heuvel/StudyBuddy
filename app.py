from flask import Flask, render_template, redirect, url_for, session, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import init_db, get_db
from algorithm import genereer_schema
import requests

app = Flask(__name__)
app.secret_key = "studybuddy_secret_2026"

# ── HELPERS ──────────────────────────────────────────────
def ingelogd():
    return "user_id" in session

# ── AUTH ─────────────────────────────────────────────────
@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed = generate_password_hash(password)
        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed)
            )
            db.commit()
 
            # Haal de nieuwe user op
            user = db.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,)
            ).fetchone()
 
            # Standaard vakken toevoegen
            standaard_vakken = [
                "Wiskunde", "Nederlands", "Engels", "Biologie",
                "Scheikunde", "Natuurkunde", "Geschiedenis",
                "Aardrijkskunde", "Economie", "Duits"
            ]
            for vak in standaard_vakken:
                db.execute(
                    "INSERT INTO vakken (user_id, naam) VALUES (?, ?)",
                    (user["id"], vak)
                )
            db.commit()
 
            flash("Account aangemaakt! Je kunt nu inloggen.", "success")
            return redirect(url_for("login"))
        except:
            flash("Gebruikersnaam bestaat al.", "error")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        else:
            flash("Verkeerde gebruikersnaam of wachtwoord.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ── DASHBOARD ─────────────────────────────────────────────
@app.route("/dashboard")
def dashboard():
    if not ingelogd():
        return redirect(url_for("login"))
    db = get_db()
    try:
        response = requests.get("https://zenquotes.io/api/random", timeout=3)
        quote_data = response.json()[0]
        quote = f"{quote_data['q']} — {quote_data['a']}"
    except:
        quote = "Blijf gefocust en werk hard!"

    taken_vandaag = db.execute("""
        SELECT * FROM taken 
        WHERE user_id = ? AND voltooid = 0
        ORDER BY prioriteit DESC
    """, (session["user_id"],)).fetchall()

    totaal = db.execute(
        "SELECT COUNT(*) FROM taken WHERE user_id = ?",
        (session["user_id"],)
    ).fetchone()[0]

    voltooid = db.execute(
        "SELECT COUNT(*) FROM taken WHERE user_id = ? AND voltooid = 1",
        (session["user_id"],)
    ).fetchone()[0]

    voortgang = round((voltooid / totaal * 100) if totaal > 0 else 0)

    return render_template("dashboard.html",
        quote=quote,
        taken=taken_vandaag,
        voortgang=voortgang,
        voltooid=voltooid,
        totaal=totaal
    )

# ── TAKEN ─────────────────────────────────────────────────
@app.route("/taken")
def taken():
    if not ingelogd():
        return redirect(url_for("login"))
    db = get_db()
    open_taken = db.execute("""
        SELECT t.*, v.naam as vak_naam 
        FROM taken t LEFT JOIN vakken v ON t.vak_id = v.id 
        WHERE t.user_id = ? AND t.voltooid = 0 
        ORDER BY t.prioriteit DESC
    """, (session["user_id"],)).fetchall()
    afgerond = db.execute("""
        SELECT t.*, v.naam as vak_naam 
        FROM taken t LEFT JOIN vakken v ON t.vak_id = v.id 
        WHERE t.user_id = ? AND t.voltooid = 1
    """, (session["user_id"],)).fetchall()
    return render_template("tasks.html", open_taken=open_taken, afgerond=afgerond)

@app.route("/taak/nieuw", methods=["GET", "POST"])
def taak_nieuw():
    if not ingelogd():
        return redirect(url_for("login"))
    db = get_db()
    vakken = db.execute(
        "SELECT * FROM vakken WHERE user_id = ?",
        (session["user_id"],)
    ).fetchall()
    if request.method == "POST":
        db.execute("""
            INSERT INTO taken (user_id, vak_id, titel, beschrijving, deadline, moeilijkheid, prioriteit)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            request.form["vak_id"],
            request.form["titel"],
            request.form["beschrijving"],
            request.form["deadline"],
            request.form["moeilijkheid"],
            request.form["prioriteit"]
        ))
        db.commit()
        flash("Taak aangemaakt!", "success")
        return redirect(url_for("taken"))
    return render_template("task_form.html", vakken=vakken, taak=None)

@app.route("/taak/bewerken/<int:taak_id>", methods=["GET", "POST"])
def taak_bewerken(taak_id):
    if not ingelogd():
        return redirect(url_for("login"))
    db = get_db()
    taak = db.execute(
        "SELECT * FROM taken WHERE id = ? AND user_id = ?",
        (taak_id, session["user_id"])
    ).fetchone()
    vakken = db.execute(
        "SELECT * FROM vakken WHERE user_id = ?",
        (session["user_id"],)
    ).fetchall()
    if request.method == "POST":
        db.execute("""
            UPDATE taken SET titel=?, beschrijving=?, deadline=?, 
            moeilijkheid=?, prioriteit=?, vak_id=?
            WHERE id=? AND user_id=?
        """, (
            request.form["titel"],
            request.form["beschrijving"],
            request.form["deadline"],
            request.form["moeilijkheid"],
            request.form["prioriteit"],
            request.form["vak_id"],
            taak_id,
            session["user_id"]
        ))
        db.commit()
        flash("Taak bijgewerkt!", "success")
        return redirect(url_for("taken"))
    return render_template("task_form.html", vakken=vakken, taak=taak)

@app.route("/taak/voltooien/<int:taak_id>")
def taak_voltooien(taak_id):
    if not ingelogd():
        return redirect(url_for("login"))
    db = get_db()
    db.execute(
        "UPDATE taken SET voltooid = 1 WHERE id = ? AND user_id = ?",
        (taak_id, session["user_id"])
    )
    db.commit()
    return redirect(url_for("taken"))

@app.route("/taak/heropenen/<int:taak_id>")
def taak_heropenen(taak_id):
    if not ingelogd():
        return redirect(url_for("login"))
    db = get_db()
    db.execute(
        "UPDATE taken SET voltooid = 0 WHERE id = ? AND user_id = ?",
        (taak_id, session["user_id"])
    )
    db.commit()
    return redirect(url_for("taken"))

@app.route("/taak/verwijderen/<int:taak_id>")
def taak_verwijderen(taak_id):
    if not ingelogd():
        return redirect(url_for("login"))
    db = get_db()
    db.execute(
        "DELETE FROM taken WHERE id = ? AND user_id = ?",
        (taak_id, session["user_id"])
    )
    db.commit()
    return redirect(url_for("taken"))

# ── SCHEMA ────────────────────────────────────────────────
@app.route("/schema")
def schema():
    if not ingelogd():
        return redirect(url_for("login"))
    db = get_db()
    taken = db.execute(
        "SELECT * FROM taken WHERE user_id = ? AND voltooid = 0",
        (session["user_id"],)
    ).fetchall()
    instelling = db.execute(
        "SELECT * FROM instellingen WHERE user_id = ?",
        (session["user_id"],)
    ).fetchone()
    uren_per_dag = instelling["uren_per_dag"] if instelling else 4
    studieschema = genereer_schema(taken, uren_per_dag)
    return render_template("schedule.html", schema=studieschema)

# ── INSTELLINGEN ──────────────────────────────────────────
@app.route("/instellingen", methods=["GET", "POST"])
def instellingen():
    if not ingelogd():
        return redirect(url_for("login"))
    db = get_db()
    if request.method == "POST":
        vak_naam = request.form.get("vak_naam")
        if vak_naam:
            db.execute(
                "INSERT INTO vakken (user_id, naam) VALUES (?, ?)",
                (session["user_id"], vak_naam)
            )
        uren = request.form.get("uren_per_dag")
        if uren:
            bestaand = db.execute(
                "SELECT * FROM instellingen WHERE user_id = ?",
                (session["user_id"],)
            ).fetchone()
            if bestaand:
                db.execute(
                    "UPDATE instellingen SET uren_per_dag = ? WHERE user_id = ?",
                    (uren, session["user_id"])
                )
            else:
                db.execute(
                    "INSERT INTO instellingen (user_id, uren_per_dag) VALUES (?, ?)",
                    (session["user_id"], uren)
                )
        db.commit()
        flash("Instellingen opgeslagen!", "success")
        return redirect(url_for("instellingen"))

    vakken = db.execute(
        "SELECT * FROM vakken WHERE user_id = ?",
        (session["user_id"],)
    ).fetchall()
    instelling = db.execute(
        "SELECT * FROM instellingen WHERE user_id = ?",
        (session["user_id"],)
    ).fetchone()
    user = db.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()
    return render_template("settings.html", vakken=vakken, instellingen=instelling, user=user)

@app.route("/vak/verwijderen/<int:vak_id>")
def vak_verwijderen(vak_id):
    if not ingelogd():
        return redirect(url_for("login"))
    db = get_db()
    db.execute(
        "DELETE FROM vakken WHERE id = ? AND user_id = ?",
        (vak_id, session["user_id"])
    )
    db.commit()
    return redirect(url_for("instellingen"))

# ── PROFIEL ───────────────────────────────────────────────
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def toegestaan_bestand(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/profiel", methods=["GET", "POST"])
def profiel():
    if not ingelogd():
        return redirect(url_for("login"))
    db = get_db()
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        telefoon = request.form.get("telefoonnummer")
        nieuw_wachtwoord = request.form.get("password")

        # Foto uploaden
        foto_naam = None
        if 'foto' in request.files:
            foto = request.files['foto']
            if foto and foto.filename != '' and toegestaan_bestand(foto.filename):
                foto_naam = secure_filename(f"user_{session['user_id']}_{foto.filename}")
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                foto.save(os.path.join(app.config['UPLOAD_FOLDER'], foto_naam))

        if nieuw_wachtwoord:
            hashed = generate_password_hash(nieuw_wachtwoord)
            if foto_naam:
                db.execute("""
                    UPDATE users SET username=?, email=?, telefoonnummer=?, password=?, foto=?
                    WHERE id=?
                """, (username, email, telefoon, hashed, foto_naam, session["user_id"]))
            else:
                db.execute("""
                    UPDATE users SET username=?, email=?, telefoonnummer=?, password=?
                    WHERE id=?
                """, (username, email, telefoon, hashed, session["user_id"]))
        else:
            if foto_naam:
                db.execute("""
                    UPDATE users SET username=?, email=?, telefoonnummer=?, foto=?
                    WHERE id=?
                """, (username, email, telefoon, foto_naam, session["user_id"]))
            else:
                db.execute("""
                    UPDATE users SET username=?, email=?, telefoonnummer=?
                    WHERE id=?
                """, (username, email, telefoon, session["user_id"]))

        db.commit()
        session["username"] = username
        flash("Profiel opgeslagen!", "success")
        return redirect(url_for("profiel"))

    user = db.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()
    return render_template("profiel.html", user=user)

# ── START ─────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    app.run(debug=True)

    