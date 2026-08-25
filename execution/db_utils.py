import sqlite3
import os

_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bids_db.sqlite")

def init_db():
    conn = sqlite3.connect(_db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS bids (
            id TEXT PRIMARY KEY,
            title TEXT,
            organization TEXT,
            start_date TEXT,
            deadline TEXT,
            category TEXT,
            source TEXT,
            url TEXT,
            description TEXT,
            inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_bids_to_db(bids):
    init_db()
    conn = sqlite3.connect(_db_path)
    c = conn.cursor()
    new_count = 0
    for bid in bids:
        try:
            c.execute('''
                INSERT INTO bids (id, title, organization, start_date, deadline, category, source, url, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                bid.get("id", ""),
                bid.get("title", ""),
                bid.get("organization", ""),
                bid.get("start", ""),
                bid.get("deadline", ""),
                bid.get("category", ""),
                bid.get("source", ""),
                bid.get("url", ""),
                bid.get("description", "")
            ))
            new_count += 1
        except sqlite3.IntegrityError:
            pass # Already exists
    conn.commit()
    conn.close()
    return new_count

def get_recent_custom_bids(days=7):
    init_db()
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute(f"SELECT * FROM bids WHERE inserted_at >= datetime('now', '-{days} days')")
    rows = c.fetchall()
    conn.close()
    
    keywords = ["게임", "유저", "ai"]
    matched = []
    for row in rows:
        title = row["title"].lower()
        if any(k in title for k in keywords):
            matched.append(dict(row))
    return matched
