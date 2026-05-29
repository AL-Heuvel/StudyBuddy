import os
import sqlite3

from werkzeug.security import generate_password_hash
 
def get_db():
    conn = sqlite3.connect("studybuddy.db")
    conn.row_factory = sqlite3.Row
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

    cursor.execute("PRAGMA table_info(users)")
    column_names = [column[1] for column in cursor.fetchall()]

    if "is_admin" not in column_names:
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
 
    conn.commit()

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