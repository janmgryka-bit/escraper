import sqlite3
from datetime import datetime
import hashlib

class Database:
    def __init__(self, db_path='hunter_final.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        # PANCERNA baza danych z content_id jako UNIQUE
        conn.execute('''CREATE TABLE IF NOT EXISTS offers 
                       (content_id TEXT UNIQUE, content_hash TEXT, url TEXT, title TEXT, price TEXT, 
                        source TEXT, date_added TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS fb_notifications 
                       (notification_id TEXT PRIMARY KEY, group_name TEXT, content TEXT, 
                        post_url TEXT, date_added TEXT)''')
        conn.commit()
        conn.close()
    
    def generate_content_hash(self, title, price, description, location=None):
        """
        Generuje unikalny hash oferty na podstawie tytułu, ceny, opisu i lokalizacji.
        Pancerne rozwiązanie przeciw duplikatom - niezależne od URL.
        """
        # Tytuł - małe litery, bez spacji i znaków specjalnych
        title_clean = "".join(title.lower().strip().split()) if title else ""
        
        # Cena - tylko cyfry (usuń zł, pln, spacje itp.)
        price_clean = "".join(filter(str.isdigit, str(price))) if price else ""
        
        # Opis - pierwsze 150 znaków, małe litery, bez spacji i znaków specjalnych
        desc_part = description[:150].lower().strip() if description else ""
        desc_clean = "".join(desc_part.split())
        
        # Lokalizacja - jeśli podana
        location_clean = "".join(location.lower().strip().split()) if location else ""
        
        # Połącz wszystkie elementy w unikalny ciąg
        unique_string = f"{title_clean}{price_clean}{desc_clean}{location_clean}"
        
        # Generuj hash
        hash_result = hashlib.md5(unique_string.encode()).hexdigest()
        
        print(f"DEBUG: content_hash = {hash_result[:8]}...")
        print(f"  - title_clean: {title_clean[:30]}...")
        print(f"  - price_clean: {price_clean}")
        print(f"  - desc_clean: {desc_clean[:50]}...")
        print(f"  - location_clean: {location_clean[:20]}...")
        
        return hash_result
    
    def is_duplicate(self, content_id):
        """PANCERNE sprawdzenie duplikatu na podstawie content_id"""
        conn = sqlite3.connect(self.db_path)
        result = conn.execute("SELECT 1 FROM offers WHERE content_id=?", (content_id,)).fetchone()
        conn.close()
        return result is not None
    
    def offer_exists(self, title, price, description, location=None):
        """Sprawdź czy oferta istnieje na podstawie content_hash (pancerne rozwiązanie)"""
        content_hash = self.generate_content_hash(title, price, description, location)
        conn = sqlite3.connect(self.db_path)
        result = conn.execute("SELECT 1 FROM offers WHERE content_hash=?", (content_hash,)).fetchone()
        conn.close()
        return result is not None
    
    def add_offer_with_content_id(self, content_id, title, price, description, url, location=None, source='olx'):
        """PANCERNE dodawanie oferty z content_id - INSERT OR IGNORE"""
        # Czyść URL - usuń wszystko po ?
        clean_url = url.split('?')[0] if '?' in url else url
        
        conn = sqlite3.connect(self.db_path)
        try:
            # INSERT OR IGNORE - 100% pewności, że nie będzie duplikatów
            conn.execute("""INSERT OR IGNORE INTO offers 
                          (content_id, content_hash, url, title, price, source, date_added) 
                          VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                        (content_id, 
                         self.generate_content_hash(title, price, description, location),
                         clean_url, title, str(price), source, datetime.now().isoformat()))
            conn.commit()
            
            # Sprawdź czy insert się powiódł
            if conn.total_changes > 0:
                print(f"DEBUG: Oferta zapisana do bazy: {content_id[:30]}...")
                return True
            else:
                print(f"DEBUG: Oferta już istnieje (INSERT OR IGNORE): {content_id[:30]}...")
                return False
        except Exception as e:
            print(f"DEBUG: Błąd zapisu oferty: {e}")
            return False
        finally:
            conn.close()
    
    def add_offer(self, title, price, description, url, location=None, source='olx'):
        """Dodaj ofertę używając content_hash jako unique ID (pancerne rozwiązanie)"""
        content_hash = self.generate_content_hash(title, price, description, location)
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("INSERT INTO offers (content_hash, url, title, price, source, date_added) VALUES (?, ?, ?, ?, ?, ?)", 
                        (content_hash, url, title, str(price), source, datetime.now().isoformat()))
            conn.commit()
            print(f"DEBUG: Oferta zapisana do bazy: {content_hash[:8]}...")
            return True
        except sqlite3.IntegrityError as e:
            print(f"DEBUG: Oferta już istnieje (UNIQUE constraint): {content_hash[:8]}...")
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
