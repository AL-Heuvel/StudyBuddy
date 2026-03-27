import sqlite3
 
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
            foto TEXT
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
 
    conn.commit()
    conn.close()