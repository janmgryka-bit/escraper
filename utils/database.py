import sqlite3
from datetime import datetime
import hashlib

class Database:
    def __init__(self, db_path='hunter_final.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        # ABSOLUTE DUPLICATE LOCK - content_hash jako PRIMARY KEY
        conn.execute('''DROP TABLE IF EXISTS offers''')  # Wyczyść starą tabelę
        conn.execute('''CREATE TABLE offers 
                       (content_hash TEXT PRIMARY KEY, title TEXT, price REAL, url TEXT, 
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS fb_notifications 
                       (notification_id TEXT PRIMARY KEY, group_name TEXT, content TEXT, 
                        post_url TEXT, date_added TEXT)''')
        conn.commit()
        conn.close()
    
    def get_offer_hash(self, title, price, description, location=""):
        """
        GLOBAL HASHING ENGINE - ABSOLUTE DUPLICATE LOCK
        """
        # Połącz wszystkie elementy
        hash_string = f"{title.lower()}{str(price)}{description[:100].lower()}{location.lower()}"
        
        # Usuń WSZYSTKIE spacje i znaki specjalne
        import re
        hash_string = re.sub(r'[^a-z0-9]', '', hash_string)
        
        # Generuj hash
        content_hash = hashlib.md5(hash_string.encode()).hexdigest()
        
        print(f"DEBUG: get_offer_hash = {content_hash[:12]}...")
        print(f"  - title: {title.lower()[:30]}")
        print(f"  - price: {price}")
        print(f"  - desc[:100]: {description[:100].lower()[:50]}...")
        print(f"  - location: {location.lower()}")
        print(f"  - clean_string: {hash_string[:50]}...")
        
        return content_hash
    
    def commit_or_abort(self, content_hash, title, price, url):
        """
        COMMIT OR ABORT LOGIC - ABSOLUTE DUPLICATE LOCK
        Zwraca True jeśli sukces, False jeśli duplikat
        """
        conn = sqlite3.connect(self.db_path)
        try:
            # Próba wstawienia - jeśli content_hash istnieje, IntegrityError
            conn.execute("INSERT INTO offers (content_hash, title, price, url) VALUES (?, ?, ?, ?)", 
                        (content_hash, title, float(price), url))
            conn.commit()
            print(f"DEBUG: COMMIT SUCCESS - {content_hash[:12]}...")
            return True
        except sqlite3.IntegrityError as e:
            print(f"DEBUG: ABORT - Duplicate detected: {content_hash[:12]}...")
            return False
        except Exception as e:
            print(f"DEBUG: ABORT - Database error: {e}")
            return False
        finally:
            conn.close()
    
    def fb_notification_exists(self, description, price=0, title=None):
        """Sprawdź czy powiadomienie FB istnieje na podstawie opisu + cena + tytuł"""
        content_hash = self._create_content_hash(description, price, title)
        conn = sqlite3.connect(self.db_path)
        result = conn.execute("SELECT 1 FROM fb_notifications WHERE notification_id=?", 
                            (content_hash,)).fetchone()
        conn.close()
        return result is not None
    
    def add_fb_notification(self, description, price, group_name, post_url, title=None):
        """Dodaj powiadomienie FB używając content_hash jako unique ID (100 znaków + cena + tytuł)"""
        content_hash = self._create_content_hash(description, price, title)
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("INSERT INTO fb_notifications (notification_id, group_name, content, post_url, date_added) VALUES (?, ?, ?, ?, ?)", 
                        (content_hash, group_name, description[:500], post_url, datetime.now().isoformat()))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
