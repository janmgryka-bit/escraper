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
        conn.execute('''CREATE TABLE IF NOT EXISTS fb_notifications 
                       (notification_id TEXT PRIMARY KEY, group_name TEXT, content TEXT, 
                        post_url TEXT, date_added TEXT)''')
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
    
    def fb_notification_exists(self, notification_id):
        conn = sqlite3.connect(self.db_path)
        result = conn.execute("SELECT notification_id FROM fb_notifications WHERE notification_id=?", 
                            (notification_id,)).fetchone()
        conn.close()
        return result is not None
    
    def add_fb_notification(self, notification_id, group_name, content, post_url):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("INSERT INTO fb_notifications (notification_id, group_name, content, post_url, date_added) VALUES (?, ?, ?, ?, ?)", 
                        (notification_id, group_name, content, post_url, datetime.now().isoformat()))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
