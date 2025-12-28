import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path='hunter_final.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''CREATE TABLE IF NOT EXISTS offers 
                       (url TEXT PRIMARY KEY, title TEXT, price TEXT, date_added TEXT)''')
        conn.commit()
        conn.close()
    
    def offer_exists(self, url):
        conn = sqlite3.connect(self.db_path)
        result = conn.execute("SELECT url FROM offers WHERE url=?", (url,)).fetchone()
        conn.close()
        return result is not None
    
    def add_offer(self, url, title, price):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("INSERT INTO offers (url, title, price, date_added) VALUES (?, ?, ?, ?)", 
                        (url, title, str(price), datetime.now().isoformat()))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
