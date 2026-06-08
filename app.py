import logging

from logging.handlers import RotatingFileHandler

from flask import Flask, render_template, redirect, url_for, session, request, flash, send_file, make_response

from werkzeug.security import generate_password_hash, check_password_hash

from database import init_db, get_db

from algorithm import genereer_schema

import requests

import os

from io import BytesIO

from werkzeug.utils import secure_filename
 
app = Flask(__name__)

app.secret_key = "studybuddy_secret_2026"
 
UPLOAD_FOLDER = 'static/uploads'
ADVERTENTIE_UPLOAD_FOLDER = 'static/advertensies'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ADVERTENTIE_UPLOAD_FOLDER'] = ADVERTENTIE_UPLOAD_FOLDER
from flask import send_from_directory

@app.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')


def haal_advertentie_afbeeldingen_op():
    advertentie_map = app.config.get('ADVERTENTIE_UPLOAD_FOLDER', 'static/advertensies')
    if not os.path.isdir(advertentie_map):
        return []

    geldige_extensies = {'.png', '.jpg', '.jpeg'}
    bestanden = []

    for bestandsnaam in os.listdir(advertentie_map):
        volledig_pad = os.path.join(advertentie_map, bestandsnaam)
        if os.path.isfile(volledig_pad) and os.path.splitext(bestandsnaam)[1].lower() in geldige_extensies:
            bestanden.append((os.path.getmtime(volledig_pad), bestandsnaam))

    return [bestandsnaam for _, bestandsnaam in sorted(bestanden, reverse=True)]
 
# ── LOGGING SETUP ──────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
 
handler = RotatingFileHandler('studybuddy.log', maxBytes=10000, backupCount=3)

handler.setLevel(logging.INFO)
 
formatter = logging.Formatter(

    '[%(asctime)s] %(levelname)s - %(message)s',

    datefmt='%Y-%m-%d %H:%M:%S'

)

handler.setFormatter(formatter)
 
logger = logging.getLogger(__name__)

logger.addHandler(handler)
 
# ── HELPERS ──────────────────────────────────────────────

def ingelogd():

    return "user_id" in session
 
def toegestaan_bestand(filename):

    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def haal_actieve_advertentie_op(db):
    return db.execute(
        """
        SELECT a.id AS advertentie_id,
               a.titel,
               a.beschrijving,
               a.afbeelding,
               a.doel_url,
               c.id AS campagne_id,
               c.resterende_views,
               b.naam AS bedrijf_naam,
               t.naam AS tarief_naam,
               t.aantal_views,
               t.prijs
        FROM advertenties a
        JOIN campagnes c ON c.advertentie_id = a.id
        JOIN bedrijven b ON b.id = a.bedrijf_id
        JOIN tarieven t ON t.id = c.tarief_id
        WHERE a.actief = 1
          AND c.status = 'actief'
          AND c.resterende_views > 0
        ORDER BY RANDOM()
        LIMIT 1
        """
    ).fetchone()

def registreer_advertentie_view(db, campagne_id):
    db.execute(
        "INSERT INTO advertentie_views (campagne_id) VALUES (?)",
        (campagne_id,)
    )
    db.execute(
        "UPDATE campagnes SET resterende_views = CASE WHEN resterende_views > 0 THEN resterende_views - 1 ELSE 0 END WHERE id = ?",
        (campagne_id,)
    )

def registreer_advertentie_click(db, campagne_id):
    db.execute(
        "INSERT INTO advertentie_clicks (campagne_id) VALUES (?)",
        (campagne_id,)
    )
 
# ── AUTH ─────────────────────────────────────────────────

@app.route("/")

def index():

    return render_template("landing.html")  # ← AANGEPAST

@app.route("/landing.html")
def landing_html():
    return redirect(url_for("index"))

@app.route("/adverteren", methods=["GET", "POST"])
def adverteren():
    db = get_db()

    def render_form():
        actieve_advertentie = haal_actieve_advertentie_op(db)
        if actieve_advertentie:
            registreer_advertentie_view(db, actieve_advertentie["campagne_id"])
            db.commit()
        return render_template("advertentie_form.html", actieve_advertentie=actieve_advertentie)

    if request.method == "POST":
        bedrijf_naam = request.form.get("bedrijf_naam", "").strip()
        voornaam = request.form.get("voornaam", "").strip()
        achternaam = request.form.get("achternaam", "").strip()
        email = request.form.get("email", "").strip()
        telefoon = request.form.get("telefoon", "").strip()
        doel_advertentie = request.form.get("doel_advertentie", "").strip()
        tarieven = request.form.get("tarieven", "").strip()
        views_pakket = request.form.get("views_pakket", "").strip().lower()
        startdatum = request.form.get("startdatum", "").strip()
        afbeelding_naam = None

        verplichte_velden = [
            bedrijf_naam,
            voornaam,
            achternaam,
            email,
            telefoon,
            doel_advertentie,
            tarieven,
            views_pakket,
            startdatum,
        ]

        if not all(verplichte_velden):
            flash("Vul alle velden in.", "error")
            return render_form()

        if views_pakket not in {"starter", "basis", "premium"}:
            flash("Kies een geldig views-pakket.", "error")
            return render_form()

        if 'afbeelding' not in request.files:
            flash("Upload een advertentie-afbeelding.", "error")
            return render_form()

        afbeelding = request.files['afbeelding']

        if not afbeelding or afbeelding.filename == "":
            flash("Upload een advertentie-afbeelding.", "error")
            return render_form()

        if not toegestaan_bestand(afbeelding.filename):
            flash("Alleen PNG, JPG of JPEG-afbeeldingen zijn toegestaan.", "error")
            return render_form()

        os.makedirs(app.config['ADVERTENTIE_UPLOAD_FOLDER'], exist_ok=True)
        afbeelding_naam = secure_filename(f"ad_{bedrijf_naam}_{afbeelding.filename}")
        afbeelding.save(os.path.join(app.config['ADVERTENTIE_UPLOAD_FOLDER'], afbeelding_naam))

        try:
            db.execute(
                """
                INSERT INTO advertentie_aanvragen (
                    bedrijf_naam, voornaam, achternaam, email, telefoon,
                    doel_advertentie, tarieven, views_pakket, startdatum, afbeelding
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    bedrijf_naam,
                    voornaam,
                    achternaam,
                    email,
                    telefoon,
                    doel_advertentie,
                    tarieven,
                    views_pakket,
                    startdatum,
                    afbeelding_naam,
                ),
            )
            db.commit()
            logger.info("Nieuwe advertentieaanvraag ontvangen van %s (%s)", bedrijf_naam, email)
            flash("Bedankt! Je advertentieaanvraag is ontvangen.", "success")
            return redirect(url_for("index"))
        except Exception as e:
            logger.error(f"Fout bij opslaan advertentieaanvraag: {e}")
            flash("Er ging iets mis bij het verzenden. Probeer opnieuw.", "error")

    return render_form()

@app.route("/adverteren/download")
def adverteren_download():
    inhoud = (
        "StudyBuddy Advertentie Pakketoverzicht\n\n"
        "Starter\n"
        "- Tot 1.000 views per maand\n\n"
        "Basis\n"
        "- Tot 5.000 views per maand\n\n"
        "Premium\n"
        "- Tot 10.000 views per maand\n\n"
        "Neem contact op via het formulier op de advertentiepagina.\n"
    )
    return send_file(
        BytesIO(inhoud.encode("utf-8")),
        mimetype="text/plain",
        as_attachment=True,
        download_name="studybuddy-advertentie-pakketoverzicht.txt",
    )

@app.route("/advertentie-popup")
def advertentie_popup():
    if not ingelogd():
        return redirect(url_for("login"))

    target = session.pop("post_login_target", url_for("dashboard"))
    advertentie_afbeeldingen = haal_advertentie_afbeeldingen_op()

    if not session.pop("show_advertentie_popup", False) or not advertentie_afbeeldingen:
        return redirect(target)

    return render_template(
        "advertentie_popup.html",
        advertentie_afbeelding=advertentie_afbeeldingen[0],
        target=target,
    )

@app.route("/advertentie/klik/<int:campagne_id>")
def advertentie_click(campagne_id):
    db = get_db()
    advertentie = db.execute(
        """
        SELECT a.doel_url
        FROM advertenties a
        JOIN campagnes c ON c.advertentie_id = a.id
        WHERE c.id = ?
          AND a.actief = 1
          AND c.status = 'actief'
        """,
        (campagne_id,),
    ).fetchone()

    if not advertentie:
        return redirect(url_for("index"))

    registreer_advertentie_click(db, campagne_id)
    db.commit()

    logger.info("Advertentieklik geregistreerd voor campagne %s", campagne_id)
    return redirect(advertentie["doel_url"])
 
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
 
            user = db.execute(

                "SELECT id FROM users WHERE username = ?",

                (username,)

            ).fetchone()
 
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
 
            logger.info(f"Nieuw account aangemaakt: '{username}'")

            flash("Account aangemaakt! Je kunt nu inloggen.", "success")

            return redirect(url_for("login"))

        except Exception as e:

            logger.error(f"Fout bij registreren van '{username}': {e}")

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

            session["is_admin"] = 1 if user["is_admin"] else 0

            session["show_advertentie_popup"] = True
            session["post_login_target"] = url_for("admin_dashboard") if user["is_admin"] else url_for("dashboard")

            logger.info(f"Gebruiker '{username}' is ingelogd (admin: {bool(user['is_admin'])})")

            return redirect(url_for("advertentie_popup"))

        else:

            logger.warning(f"Mislukte inlogpoging voor gebruiker '{username}'")

            flash("Verkeerde gebruikersnaam of wachtwoord.", "error")

    return render_template("login.html")
 
@app.route("/logout")

def logout():

    username = session.get("username", "onbekend")

    logger.info(f"Gebruiker '{username}' is uitgelogd")

    session.clear()

    return redirect(url_for("login"))

# ── ADMIN ──────────────────────────────────────────────────

def is_admin():
    return bool(session.get("is_admin"))

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not ingelogd() or not is_admin():
            flash("U hebt geen toegang tot deze pagina.", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/admin")

@admin_required

def admin_dashboard():

    db = get_db()

    # Statistieken

    totaal_users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    totaal_taken = db.execute("SELECT COUNT(*) FROM taken").fetchone()[0]

    voltooide_taken = db.execute("SELECT COUNT(*) FROM taken WHERE voltooid = 1").fetchone()[0]

    admin_users = db.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1").fetchone()[0]

    # Gebruikers

    users = db.execute("""

        SELECT u.id, u.username, u.email, u.is_admin, 

               (SELECT COUNT(*) FROM taken WHERE user_id = u.id) as taken_count

        FROM users u

        ORDER BY u.is_admin DESC, u.id DESC

    """).fetchall()

    logger.info(f"Admin dashboard geopend door gebruiker {session['user_id']}")

    return render_template("admin.html",

        totaal_users=totaal_users,

        totaal_taken=totaal_taken,

        voltooide_taken=voltooide_taken,

        admin_users=admin_users,

        users=users

    )

@app.route("/admin/gebruiker/maken", methods=["GET", "POST"])

@admin_required

def admin_user_create():
    if request.method == "POST":

        username = request.form.get("username")

        password = request.form.get("password")

        email = request.form.get("email", "")

        is_admin_flag = int(request.form.get("is_admin", 0))

        db = get_db()

        try:

            hashed = generate_password_hash(password)

            db.execute(

                "INSERT INTO users (username, password, email, is_admin) VALUES (?, ?, ?, ?)",

                (username, hashed, email, is_admin_flag)

            )

            db.commit()

            user = db.execute(

                "SELECT id FROM users WHERE username = ?",

                (username,)

            ).fetchone()

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

            logger.info(f"Nieuwe gebruiker '{username}' aangemaakt door admin {session['user_id']} (is_admin: {bool(is_admin_flag)})")

            flash(f"Gebruiker '{username}' aangemaakt!", "success")

            return redirect(url_for("admin_dashboard"))

        except Exception as e:

            logger.error(f"Fout bij aanmaken gebruiker: {e}")

            flash("Gebruikersnaam bestaat al.", "error")

    return render_template("admin_user_form.html", user=None)

@app.route("/admin/gebruiker/<int:user_id>/bewerken", methods=["GET", "POST"])

@admin_required

def admin_user_edit(user_id):

    db = get_db()

    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    if not user:

        flash("Gebruiker niet gevonden.", "error")

        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":

        try:

            username = request.form.get("username")

            email = request.form.get("email", "")

            is_admin = int(request.form.get("is_admin", 0))

            password = request.form.get("password")

            if password:

                hashed = generate_password_hash(password)

                db.execute(

                    "UPDATE users SET username=?, email=?, is_admin=?, password=? WHERE id=?",

                    (username, email, is_admin, hashed, user_id)

                )

            else:

                db.execute(

                    "UPDATE users SET username=?, email=?, is_admin=? WHERE id=?",

                    (username, email, is_admin, user_id)

                )

            db.commit()

            logger.info(f"Gebruiker {user_id} bijgewerkt door admin {session['user_id']}")

            flash("Gebruiker bijgewerkt!", "success")

            return redirect(url_for("admin_dashboard"))

        except Exception as e:

            logger.error(f"Fout bij bewerken gebruiker {user_id}: {e}")

            flash("Er ging iets mis bij het bijwerken.", "error")

    return render_template("admin_user_form.html", user=user)

@app.route("/admin/gebruiker/<int:user_id>/verwijderen", methods=["POST"])

@admin_required

def admin_user_delete(user_id):

    if user_id == session["user_id"]:

        flash("U kunt uw eigen account niet verwijderen.", "error")

        return redirect(url_for("admin_dashboard"))

    db = get_db()

    try:

        # Verwijder gerelateerde gegevens

        db.execute("DELETE FROM taken WHERE user_id = ?", (user_id,))

        db.execute("DELETE FROM vakken WHERE user_id = ?", (user_id,))

        db.execute("DELETE FROM instellingen WHERE user_id = ?", (user_id,))

        db.execute("DELETE FROM favorieten WHERE user_id = ?", (user_id,))

        db.execute("DELETE FROM users WHERE id = ?", (user_id,))

        db.commit()

        logger.info(f"Gebruiker {user_id} verwijderd door admin {session['user_id']}")

        flash("Gebruiker verwijderd!", "success")

    except Exception as e:

        logger.error(f"Fout bij verwijderen gebruiker {user_id}: {e}")

        flash("Er ging iets mis bij het verwijderen.", "error")

    return redirect(url_for("admin_dashboard"))
 
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

        logger.info(f"Quote opgehaald voor gebruiker {session['user_id']}")

    except Exception as e:

        logger.error(f"Fout bij ophalen quote: {e}")

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

    logger.info(f"Takenoverzicht bekeken door gebruiker {session['user_id']}")

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

        try:

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

            logger.info(f"Nieuwe taak '{request.form['titel']}' aangemaakt door gebruiker {session['user_id']}")

            flash("Taak aangemaakt!", "success")

            return redirect(url_for("taken"))

        except Exception as e:

            logger.error(f"Fout bij aanmaken taak: {e}")

            flash("Er ging iets mis bij het aanmaken van de taak.", "error")

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

        try:

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

            logger.info(f"Taak {taak_id} bijgewerkt door gebruiker {session['user_id']}")

            flash("Taak bijgewerkt!", "success")

            return redirect(url_for("taken"))

        except Exception as e:

            logger.error(f"Fout bij bewerken taak {taak_id}: {e}")

            flash("Er ging iets mis bij het bewerken.", "error")

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

    logger.info(f"Taak {taak_id} voltooid door gebruiker {session['user_id']}")

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

    logger.info(f"Taak {taak_id} heropend door gebruiker {session['user_id']}")

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

    logger.info(f"Taak {taak_id} verwijderd door gebruiker {session['user_id']}")

    return redirect(url_for("taken"))
 
# ── SCHEMA ────────────────────────────────────────────────

@app.route("/schema")

def schema():

    if not ingelogd():

        return redirect(url_for("login"))

    db = get_db()

    try:

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

        logger.info(f"Schema gegenereerd voor gebruiker {session['user_id']}")

        return render_template("schedule.html", schema=studieschema)

    except Exception as e:

        logger.error(f"Fout bij genereren schema: {e}")

        flash("Er ging iets mis bij het laden van het schema.", "error")

        return redirect(url_for("dashboard"))
 
# ── INSTELLINGEN ──────────────────────────────────────────

@app.route("/instellingen", methods=["GET", "POST"])

def instellingen():

    if not ingelogd():

        return redirect(url_for("login"))

    db = get_db()

    if request.method == "POST":

        try:

            vak_naam = request.form.get("vak_naam")

            if vak_naam:

                db.execute(

                    "INSERT INTO vakken (user_id, naam) VALUES (?, ?)",

                    (session["user_id"], vak_naam)

                )

                logger.info(f"Vak '{vak_naam}' toegevoegd door gebruiker {session['user_id']}")

            uren = request.form.get("uren_per_dag")
            werk = request.form.get("werk_tijd")
            pauze = request.form.get("pauze_tijd")

            if uren or werk or pauze:

                bestaand = db.execute(

                    "SELECT * FROM instellingen WHERE user_id = ?",

                    (session["user_id"],)

                ).fetchone()

                if bestaand:

                    # update uren_per_dag and optionally timer values
                    if werk or pauze:
                        cur = db.execute("SELECT werk_tijd, pauze_tijd FROM instellingen WHERE user_id = ?", (session['user_id'],)).fetchone()
                        cur_werk = cur['werk_tijd'] if cur and cur['werk_tijd'] is not None else 25
                        cur_pauze = cur['pauze_tijd'] if cur and cur['pauze_tijd'] is not None else 5
                        new_werk = int(werk) if werk else cur_werk
                        new_pauze = int(pauze) if pauze else cur_pauze
                        # update all three values
                        db.execute(
                            "UPDATE instellingen SET uren_per_dag = ?, werk_tijd = ?, pauze_tijd = ? WHERE user_id = ?",
                            (uren if uren else bestaand['uren_per_dag'], new_werk, new_pauze, session["user_id"]) 
                        )
                    else:
                        db.execute(
                            "UPDATE instellingen SET uren_per_dag = ? WHERE user_id = ?",
                            (uren, session["user_id"]) 
                        )

                else:

                    # insert with optional timer values
                    vals = (
                        session["user_id"],
                        uren if uren else 4,
                        int(werk) if werk else 25,
                        int(pauze) if pauze else 5
                    )
                    db.execute(
                        "INSERT INTO instellingen (user_id, uren_per_dag, werk_tijd, pauze_tijd) VALUES (?, ?, ?, ?)",
                        vals
                    )

                logger.info(f"Instellingen bijgewerkt voor gebruiker {session['user_id']}")

            db.commit()

            flash("Instellingen opgeslagen!", "success")

            return redirect(url_for("instellingen"))

        except Exception as e:

            logger.error(f"Fout bij opslaan instellingen: {e}")

            flash("Er ging iets mis bij het opslaan.", "error")
 
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


# Inject timer settings and uploaded advert images into all templates
@app.context_processor
def inject_timer_settings():
    advertentie_map = app.config.get('ADVERTENTIE_UPLOAD_FOLDER', 'static/advertensies')
    advertentie_afbeeldingen = []
    advertentie_css_pad = os.path.join('static', 'css', 'promo-form.css')
    advertentie_css_version = int(os.path.getmtime(advertentie_css_pad)) if os.path.exists(advertentie_css_pad) else 0

    if os.path.isdir(advertentie_map):
        geldige_extensies = {'.png', '.jpg', '.jpeg'}
        bestanden = []

        for bestandsnaam in os.listdir(advertentie_map):
            volledig_pad = os.path.join(advertentie_map, bestandsnaam)
            if os.path.isfile(volledig_pad) and os.path.splitext(bestandsnaam)[1].lower() in geldige_extensies:
                bestanden.append((os.path.getmtime(volledig_pad), bestandsnaam))

        advertentie_afbeeldingen = [
            bestandsnaam for _, bestandsnaam in sorted(bestanden, reverse=True)
        ]

    try:
        if 'user_id' in session:
            db = get_db()
            inst = db.execute("SELECT werk_tijd, pauze_tijd FROM instellingen WHERE user_id = ?", (session['user_id'],)).fetchone()
            werk = inst['werk_tijd'] if inst and inst['werk_tijd'] is not None else 25
            pauze = inst['pauze_tijd'] if inst and inst['pauze_tijd'] is not None else 5
            # expose in minutes
            return dict(
                TIMER_WERK_MIN=werk,
                TIMER_PAUZE_MIN=pauze,
                advertentie_afbeeldingen=advertentie_afbeeldingen,
                advertentie_css_version=advertentie_css_version,
            )
    except Exception:
        pass
    return dict(
        TIMER_WERK_MIN=25,
        TIMER_PAUZE_MIN=5,
        advertentie_afbeeldingen=[],
        advertentie_css_version=advertentie_css_version,
    )
 
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

    logger.info(f"Vak {vak_id} verwijderd door gebruiker {session['user_id']}")

    return redirect(url_for("instellingen"))
 
# ── PROFIEL ───────────────────────────────────────────────

@app.route("/profiel", methods=["GET", "POST"])

def profiel():

    if not ingelogd():

        return redirect(url_for("login"))

    db = get_db()

    if request.method == "POST":

        try:

            username = request.form.get("username")

            email = request.form.get("email")

            telefoon = request.form.get("telefoonnummer")

            nieuw_wachtwoord = request.form.get("password")
 
            foto_naam = None

            if 'foto' in request.files:

                foto = request.files['foto']

                if foto and foto.filename != '' and toegestaan_bestand(foto.filename):

                    foto_naam = secure_filename(f"user_{session['user_id']}_{foto.filename}")

                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

                    foto.save(os.path.join(app.config['UPLOAD_FOLDER'], foto_naam))

                    logger.info(f"Profielfoto geüpload door gebruiker {session['user_id']}")
 
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

            logger.info(f"Profiel bijgewerkt door gebruiker {session['user_id']}")

            flash("Profiel opgeslagen!", "success")

            return redirect(url_for("profiel"))

        except Exception as e:

            logger.error(f"Fout bij bijwerken profiel: {e}")

            flash("Er ging iets mis bij het opslaan.", "error")
 
    user = db.execute(

        "SELECT * FROM users WHERE id = ?",

        (session["user_id"],)

    ).fetchone()

    return render_template("profiel.html", user=user)
 
init_db()

@app.route("/factuur")
def factuur():
    if not ingelogd():
        return redirect(url_for("login"))

    try:
        from factuur import maak_factuur
    except ModuleNotFoundError:
        logger.error("Factuur-export niet beschikbaar: reportlab ontbreekt")
        flash("Factuur-export is tijdelijk niet beschikbaar.", "error")
        return redirect(url_for("instellingen"))

    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    pdf_bytes, factuurnummer = maak_factuur(user)

    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=factuur_{factuurnummer}.pdf'

    logger.info(f"Factuur {factuurnummer} gedownload door gebruiker {session['user_id']}")
    return response


# ── START ─────────────────────────────────────────────────

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000, debug=False)