import sqlite3
from datetime import datetime
import hashlib

class Database:
    def __init__(self, db_path='hunter_final.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''CREATE TABLE IF NOT EXISTS offers 
                       (content_hash TEXT PRIMARY KEY, url TEXT, title TEXT, price TEXT, 
                        source TEXT, date_added TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS fb_notifications 
                       (notification_id TEXT PRIMARY KEY, group_name TEXT, content TEXT, 
                        post_url TEXT, date_added TEXT)''')
        conn.commit()
        conn.close()
    
    def _create_content_hash(self, description, price=None):
        """Tworzy hash z pierwszych 100 znaków opisu + cena (zgodnie z wymaganiami)"""
        # Pierwsze 100 znaków opisu
        desc_part = description[:100].lower().strip()
        # Usuń białe znaki dla lepszego porównania
        desc_clean = "".join(desc_part.split())
        
        # Dodaj cenę jeśli podana
        if price is not None:
            unique_string = f"{desc_clean}{price}"
        else:
            unique_string = desc_clean
        
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    def offer_exists(self, description, price):
        """Sprawdź czy oferta istnieje na podstawie opisu (100 znaków) + cena"""
        content_hash = self._create_content_hash(description, price)
        conn = sqlite3.connect(self.db_path)
        result = conn.execute("SELECT content_hash FROM offers WHERE content_hash=?", (content_hash,)).fetchone()
        conn.close()
        return result is not None
    
    def add_offer(self, description, price, url, title, source='olx'):
        """Dodaj ofertę używając content_hash jako unique ID (100 znaków opisu + cena)"""
        content_hash = self._create_content_hash(description, price)
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("INSERT INTO offers (content_hash, url, title, price, source, date_added) VALUES (?, ?, ?, ?, ?, ?)", 
                        (content_hash, url, title, str(price), source, datetime.now().isoformat()))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def fb_notification_exists(self, description, price=0):
        """Sprawdź czy powiadomienie FB istnieje na podstawie opisu + cena"""
        content_hash = self._create_content_hash(description, price)
        conn = sqlite3.connect(self.db_path)
        result = conn.execute("SELECT notification_id FROM fb_notifications WHERE notification_id=?", 
                            (content_hash,)).fetchone()
        conn.close()
        return result is not None
    
    def add_fb_notification(self, description, price, group_name, post_url):
        """Dodaj powiadomienie FB używając content_hash jako unique ID (100 znaków + cena)"""
        content_hash = self._create_content_hash(description, price)
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
