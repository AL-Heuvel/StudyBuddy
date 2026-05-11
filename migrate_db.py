#!/usr/bin/env python3
"""
Migratie script voor bestaande databases
Voegt is_admin kolom toe aan users tabel als deze ontbreekt
"""

import sqlite3
import os

def migrate_database():
    db_path = "studybuddy.db"
    
    if not os.path.exists(db_path):
        print("❌ Database niet gevonden. Start eerst de app.")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check of kolom al bestaat
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if "is_admin" not in column_names:
            print("🔄 Migratie nodig: is_admin kolom ontbreekt...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
            conn.commit()
            print("✅ is_admin kolom toegevoegd!")
        else:
            print("✅ is_admin kolom bestaat al")
        
        # Toon alle users
        cursor.execute("SELECT id, username, email, is_admin FROM users")
        users = cursor.fetchall()
        
        print(f"\n📊 Total users: {len(users)}")
        print("-" * 80)
        print(f"{'ID':<5} {'Username':<20} {'Email':<35} {'Admin':<8}")
        print("-" * 80)
        for user in users:
            is_admin = "✓ YES" if user[3] else "✗ NO"
            print(f"{user[0]:<5} {user[1]:<20} {user[2]:<35} {is_admin:<8}")
        print("-" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ Migratiesfout: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
