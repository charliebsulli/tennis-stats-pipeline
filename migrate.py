import sqlite3
import os

MIGRATIONS_DIR = "migrations"

def run_migrations(conn):
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS migrations (
            filename    TEXT PRIMARY KEY,
            applied_at  TEXT NOT NULL
        )
    """)

    applied = {row[0] for row in cursor.execute("SELECT filename FROM migrations")}
    
    files = sorted(f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".sql"))
    
    for filename in files:
        if filename not in applied:
            print(f"Applying {filename}...")
            with open(f"{MIGRATIONS_DIR}/{filename}") as f:
                cursor.executescript(f.read())
            cursor.execute(
                "INSERT INTO migrations VALUES (?, datetime('now'))",
                (filename,)
            )
    
    conn.commit()


if __name__ == "__main__":
    conn = sqlite3.connect("tennis.db")
    run_migrations(conn)
    conn.close()