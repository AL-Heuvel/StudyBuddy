import os
import sqlite3

from werkzeug.security import generate_password_hash
 
def get_db():
    conn = sqlite3.connect("studybuddy.db", timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
 
    # Gebruikers tabel
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT,
            telefoonnummer TEXT,
            foto TEXT,
            is_admin INTEGER DEFAULT 0
        )
    """)
 
    # Vakken tabel
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vakken (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            naam TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
 
    # Taken tabel
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS taken (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vak_id INTEGER,
            titel TEXT NOT NULL,
            beschrijving TEXT,
            deadline TEXT,
            moeilijkheid TEXT CHECK(moeilijkheid IN ('laag','gemiddeld','hoog')),
            prioriteit INTEGER CHECK(prioriteit BETWEEN 1 AND 5),
            voltooid INTEGER DEFAULT 0,
            aangemaakt_op TEXT DEFAULT (date('now')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (vak_id) REFERENCES vakken(id)
        )
    """)
 
    # Instellingen tabel
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS instellingen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            uren_per_dag INTEGER DEFAULT 4,
            werk_tijd INTEGER DEFAULT 25,
            pauze_tijd INTEGER DEFAULT 5,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
 
    # Favoriete quotes tabel
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorieten (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            quote TEXT NOT NULL,
            auteur TEXT,
            opgeslagen_op TEXT DEFAULT (date('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Advertenties / advertentieplatform tabelstructuur
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bedrijven (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            naam TEXT NOT NULL,
            email TEXT NOT NULL,
            telefoon TEXT,
            adres TEXT,
            aangemaakt_op DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS advertenties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bedrijf_id INTEGER NOT NULL,
            titel TEXT NOT NULL,
            beschrijving TEXT,
            afbeelding TEXT NOT NULL,
            doel_url TEXT NOT NULL,
            actief INTEGER DEFAULT 1,
            FOREIGN KEY (bedrijf_id) REFERENCES bedrijven(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tarieven (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            naam TEXT NOT NULL,
            aantal_views INTEGER NOT NULL,
            prijs DECIMAL(10,2) NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campagnes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            advertentie_id INTEGER NOT NULL,
            tarief_id INTEGER NOT NULL,
            start_datum DATE,
            eind_datum DATE,
            resterende_views INTEGER NOT NULL,
            status TEXT DEFAULT 'actief',
            FOREIGN KEY (advertentie_id) REFERENCES advertenties(id),
            FOREIGN KEY (tarief_id) REFERENCES tarieven(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS advertentie_views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campagne_id INTEGER NOT NULL,
            bekeken_op DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (campagne_id) REFERENCES campagnes(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS advertentie_clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campagne_id INTEGER NOT NULL,
            geklikt_op DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (campagne_id) REFERENCES campagnes(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS facturen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bedrijf_id INTEGER NOT NULL,
            campagne_id INTEGER NOT NULL,
            factuurdatum DATETIME DEFAULT CURRENT_TIMESTAMP,
            bedrag DECIMAL(10,2) NOT NULL,
            betaald INTEGER DEFAULT 0,
            FOREIGN KEY (bedrijf_id) REFERENCES bedrijven(id),
            FOREIGN KEY (campagne_id) REFERENCES campagnes(id)
        )
    """)

    # Advertentie aanvragen tabel
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS advertentie_aanvragen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bedrijf_naam TEXT NOT NULL,
            voornaam TEXT NOT NULL,
            achternaam TEXT NOT NULL,
            email TEXT NOT NULL,
            telefoon TEXT NOT NULL,
            doel_advertentie TEXT NOT NULL,
            doel_url TEXT,
            afbeelding TEXT,
            tarieven TEXT NOT NULL,
            views_pakket TEXT NOT NULL CHECK(views_pakket IN ('starter', 'basis', 'premium')),
            startdatum TEXT NOT NULL,
            aangemaakt_op TEXT DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("PRAGMA table_info(advertentie_aanvragen)")
    aanvraag_columns = [column[1] for column in cursor.fetchall()]

    if "afbeelding" not in aanvraag_columns:
        cursor.execute("ALTER TABLE advertentie_aanvragen ADD COLUMN afbeelding TEXT")
        aanvraag_columns.append('afbeelding')

    if "doel_url" not in aanvraag_columns:
        cursor.execute("ALTER TABLE advertentie_aanvragen ADD COLUMN doel_url TEXT")
        aanvraag_columns.append('doel_url')

    if "user_id" not in aanvraag_columns:
        cursor.execute("ALTER TABLE advertentie_aanvragen ADD COLUMN user_id INTEGER")
        aanvraag_columns.append('user_id')

    if "status" not in aanvraag_columns:
        cursor.execute("ALTER TABLE advertentie_aanvragen ADD COLUMN status TEXT DEFAULT 'pending'")
        aanvraag_columns.append('status')

    cursor.execute("PRAGMA table_info(users)")
    column_names = [column[1] for column in cursor.fetchall()]

    if "is_admin" not in column_names:
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")

    cursor.execute("SELECT COUNT(*) FROM bedrijven")
    has_bedrijven = cursor.fetchone()[0] > 0

    if not has_bedrijven:
        cursor.execute(
            "INSERT INTO tarieven (naam, aantal_views, prijs) VALUES (?, ?, ?)",
            ("Starter", 100, 10.00),
        )
        starter_tarief_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO tarieven (naam, aantal_views, prijs) VALUES (?, ?, ?)",
            ("Basic", 500, 40.00),
        )
        cursor.execute(
            "INSERT INTO tarieven (naam, aantal_views, prijs) VALUES (?, ?, ?)",
            ("Premium", 1000, 70.00),
        )

        cursor.execute(
            """
            INSERT INTO bedrijven (naam, email, telefoon, adres)
            VALUES (?, ?, ?, ?)
            """,
            ("Fietswinkel Rotterdam", "info@fietswinkel.nl", "0101234567", "Coolsingel 1 Rotterdam"),
        )
        bedrijf_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO advertenties (bedrijf_id, titel, beschrijving, afbeelding, doel_url)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                bedrijf_id,
                "Nieuwe E-Bikes Binnen",
                "Bekijk onze nieuwste collectie elektrische fietsen",
                "ebikes.jpg",
                "https://www.fietswinkel.nl",
            ),
        )
        advertentie_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO campagnes (advertentie_id, tarief_id, start_datum, eind_datum, resterende_views)
            VALUES (?, ?, ?, ?, ?)
            """,
            (advertentie_id, starter_tarief_id, "2026-06-05", "2026-07-05", 100),
        )
        campagne_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO facturen (bedrijf_id, campagne_id, bedrag)
            VALUES (?, ?, ?)
            """,
            (bedrijf_id, campagne_id, 10.00),
        )
 
    conn.commit()

    # Meldingen (notificaties voor gebruikers)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meldingen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            bericht TEXT NOT NULL,
            gelezen INTEGER DEFAULT 0,
            aangemaakt_op DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    admin_username = os.getenv("STUDYBUDDY_ADMIN_USERNAME", "admin")
    admin_password = os.getenv("STUDYBUDDY_ADMIN_PASSWORD", "admin123")
    admin_email = os.getenv("STUDYBUDDY_ADMIN_EMAIL", "admin@studybuddy.local")

    cursor.execute("SELECT id FROM users WHERE username = ?", (admin_username,))
    admin_user = cursor.fetchone()

    if admin_user is None:
        cursor.execute(
            "INSERT INTO users (username, password, email, is_admin) VALUES (?, ?, ?, 1)",
            (admin_username, generate_password_hash(admin_password), admin_email),
        )
    else:
        cursor.execute(
            "UPDATE users SET is_admin = 1 WHERE username = ?",
            (admin_username,),
        )

    conn.commit()
    conn.close()