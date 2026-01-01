#!/usr/bin/env python3
"""
Skrypt do czyszczenia i naprawiania linków Facebook w config.yaml
Usuwa niepoprawne linki i konwertuje je na poprawne formaty.
"""

import yaml
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_facebook_links():
    """Czyści i naprawia linki Facebook w config.yaml"""
    
    try:
        # Wczytaj config
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        fb_config = config.get('facebook', {})
        priority_groups = fb_config.get('priority_groups', [])
        
        logger.info(f"🔍 Przed czyszczeniem: {len(priority_groups)} grup")
        
        cleaned_groups = []
        removed_count = 0
        
        for link in priority_groups:
            # Sprawdź czy link jest poprawny
            if is_valid_facebook_link(link):
                cleaned_groups.append(clean_facebook_link(link))
                logger.info(f"✅ Zachowano: {link}")
            else:
                removed_count += 1
                logger.warning(f"❌ Usunięto niepoprawny link: {link}")
        
        # Aktualizuj config
        fb_config['priority_groups'] = cleaned_groups
        config['facebook'] = fb_config
        
        # Zapisz config
        with open('config.yaml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"🧹 [CLEANER] Usunięto {removed_count} niepoprawnych linków")
        logger.info(f"✅ [CLEANER] Pozostało {len(cleaned_groups)} poprawnych grup")
        
        return len(cleaned_groups)
        
    except Exception as e:
        logger.error(f"❌ [CLEANER] Błąd czyszczenia linków: {e}")
        return 0

def is_valid_facebook_link(link):
    """Sprawdza czy link Facebook jest poprawny"""
    
    # Niepoprawne wzory
    invalid_patterns = [
        r'/posts/\d+/',           # Linki do konkretnych postów
        r'/user/\d+/',            # Linki do konkretnych użytkowników
        r'/joints/',              # Linki do join pages
        r'/discover/',            # Linki do discover
        r'/feed/',                # Linki do feed
        r'/groups/$',             # Linki do ogólnej strony grup
        r'/groups/$',             # Linki do pustej strony grup
    ]
    
    # Poprawny wzór: https://www.facebook.com/groups/[ID]
    valid_pattern = r'https://www\.facebook\.com/groups/\d+/[^/]*$'
    
    # Sprawdź czy nie pasuje do niepoprawnych wzorów
    for pattern in invalid_patterns:
        if re.search(pattern, link):
            return False
    
    # Sprawdź czy pasuje do poprawnego wzoru
    if re.search(valid_pattern, link):
        return True
    
    # Akceptuj też linki z nazwami grup (bez ID numerycznego)
    name_pattern = r'https://www\.facebook\.com/groups/[a-zA-Z0-9_-]+$'
    if re.search(name_pattern, link):
        return True
    
    return False

def clean_facebook_link(link):
    """Czyści i normalizuje link Facebook"""
    
    # Usuń trailing slash
    link = link.rstrip('/')
    
    # Jeśli to link z postem, wyodrębnij tylko link do grupy
    if '/posts/' in link:
        link = link.split('/posts/')[0]
    
    # Jeśli to link z user, wyodrębnij tylko link do grupy
    if '/user/' in link:
        link = link.split('/user/')[0]
    
    # Upewnij się że ma poprawny format
    if not link.startswith('https://www.facebook.com/groups/'):
        return link  # Zostaw jak jest jeśli nie pasuje do wzoru
    
    return link

if __name__ == "__main__":
    print("🧹 [CLEANER] Rozpoczynam czyszczenie linków Facebook...")
    result = clean_facebook_links()
    print(f"✅ [CLEANER] Zakończono. Pozostało {result} poprawnych grup.")
