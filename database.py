import sqlite3
import pandas as pd
import os

DB_PATH = "research.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Saved Items Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            headline TEXT NOT NULL,
            link TEXT UNIQUE NOT NULL,
            firm TEXT,
            region TEXT,
            topic TEXT,
            impact INTEGER,
            publication_date DATE,
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Custom Sources Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            domain TEXT UNIQUE NOT NULL,
            category TEXT,
            last_sync TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_article(article_data):
    """Saves an article to the saved_items table."""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute('''
            INSERT INTO saved_items (headline, link, firm, region, topic, impact, publication_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            article_data['Headline'], 
            article_data['Link'], 
            article_data['Firm'], 
            article_data['Region'], 
            article_data['Topic'], 
            article_data['Impact'],
            article_data['Date']
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Already saved
    finally:
        conn.close()

def get_saved_articles():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM saved_items ORDER BY saved_at DESC", conn)
    conn.close()
    return df

def remove_saved_article(link):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM saved_items WHERE link = ?", (link,))
    conn.commit()
    conn.close()

def add_source(name, domain, category):
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("INSERT INTO sources (name, domain, category) VALUES (?, ?, ?)", (name, domain, category))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_sources():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM sources", conn)
    conn.close()
    return df

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
