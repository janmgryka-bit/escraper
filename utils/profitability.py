import re
import logging

logger = logging.getLogger('escraper.profitability')

class ProfitabilityCalculator:
    def __init__(self, config_loader):
        self.config = config_loader
    
    def _detect_model(self, title):
        """
        Wykrywa model iPhone z tytułu/opisu.
        Zwraca znormalizowaną nazwę modelu.
        """
        title_lower = title.lower()
        
        # Sprawdź wszystkie włączone modele
        for model in self.config.get_enabled_models():
            # Usuń "iphone" z modelu żeby łatwiej matchować
            model_parts = model.replace("iphone", "").strip()
            
            if model_parts in title_lower:
                return model
        
        return None
    
    def _detect_condition(self, title, description=""):
        """
        Wykrywa stan urządzenia z tytułu/opisu.
        Zwraca: 'working', 'broken', 'locked', 'parts'
        """
        text = (title + " " + description).lower()
        
        # Zablokowany iCloud
        if any(word in text for word in ['icloud', 'zablokowany', 'locked', 'activation lock']):
            return 'locked'
        
        # Na części
        if any(word in text for word in ['na części', 'na czesci', 'parts', 'uszkodzony nie włącza']):
            return 'parts'
        
        # Uszkodzony
        if any(word in text for word in ['uszkodzony', 'pęknięty', 'rozbity', 'broken', 'cracked', 
                                          'zbity', 'damaged', 'nie działa', 'nie włącza']):
            return 'broken'
        
        # Sprawny (domyślnie)
        return 'working'
    
    def _extract_damage_details(self, title, description=""):
        """
        Wyciąga szczegóły uszkodzeń (ekran, obudowa, bateria, etc.)
        """
        text = (title + " " + description).lower()
        damages = []
        
        if any(word in text for word in ['ekran', 'wyświetlacz', 'screen', 'display']):
            damages.append('ekran')
        
        if any(word in text for word in ['obudowa', 'tył', 'plecki', 'back', 'housing']):
            damages.append('obudowa')
        
        if any(word in text for word in ['bateria', 'battery', 'akumulator']):
            damages.append('bateria')
        
        if any(word in text for word in ['aparat', 'camera', 'kamera']):
            damages.append('aparat')
        
        if any(word in text for word in ['face id', 'faceid', 'touch id']):
            damages.append('biometria')
        
        return damages
    
    def calculate(self, title, price, description=""):
        """
        Główna funkcja kalkulująca opłacalność oferty.
        
        Returns:
            dict: {
                'model': str,
                'condition': str,
                'damages': list,
                'buy_price': int,
                'market_price': int,
                'repair_cost': int,
                'total_cost': int,
                'potential_profit': int,
                'profit_margin': float,
                'is_profitable': bool,
                'recommendation': str
            }
        """
        # Wykryj model
        model = self._detect_model(title)
        if not model:
            return {
                'is_profitable': False,
                'recommendation': 'Nieznany model iPhone',
                'model': None
            }
        
        # Pobierz cennik
        pricing = self.config.get_pricing(model)
        if not pricing:
            return {
                'is_profitable': False,
                'recommendation': f'Brak cennika dla {model}',
                'model': model
            }
        
        # Wykryj stan
        condition = self._detect_condition(title, description)
        damages = self._extract_damage_details(title, description)
        
        # Pobierz odpowiednią cenę zakupu
        if condition == 'locked':
            max_buy_price = pricing['buy_max_locked']
            repair_cost = pricing['unlock_cost']  # Zwykle 0 (niemożliwe)
        elif condition == 'broken' or condition == 'parts':
            max_buy_price = pricing['buy_max_broken']
            repair_cost = pricing['repair_cost']
        else:  # working
            max_buy_price = pricing['buy_max_working']
            repair_cost = 0
        
        # Oblicz koszty i zysk
        total_cost = price + repair_cost
        market_price = pricing['market_price']
        potential_profit = market_price - total_cost
        profit_margin = (potential_profit / market_price * 100) if market_price > 0 else 0
        min_profit = pricing['min_profit']
        
        # Oceń opłacalność
        is_profitable = (
            price <= max_buy_price and 
            potential_profit >= min_profit
        )
        
        # Rekomendacja
        if is_profitable:
            if potential_profit >= min_profit * 2:
                recommendation = f"🔥 SUPER OKAZJA! Zysk: {potential_profit}zł ({profit_margin:.1f}%)"
            else:
                recommendation = f"✅ Opłacalne. Zysk: {potential_profit}zł ({profit_margin:.1f}%)"
        else:
            if price > max_buy_price:
                recommendation = f"❌ Za drogie. Max: {max_buy_price}zł (jest: {price}zł)"
            else:
                recommendation = f"⚠️ Mały zysk. Tylko {potential_profit}zł (min: {min_profit}zł)"
        
        return {
            'model': model,
            'condition': condition,
            'damages': damages,
            'buy_price': price,
            'market_price': market_price,
            'repair_cost': repair_cost,
            'total_cost': total_cost,
            'potential_profit': potential_profit,
            'profit_margin': profit_margin,
            'is_profitable': is_profitable,
            'recommendation': recommendation,
            'max_buy_price': max_buy_price,
            'min_profit': min_profit
        }
    
    def find_smart_matches(self, offers_list):
        """
        Znajduje inteligentne połączenia ofert (2 uszkodzone = 1 sprawny).
        
        Args:
            offers_list: Lista ofert z kalkulacjami
            
        Returns:
            list: Lista możliwych połączeń
        """
        if not self.config.is_smart_matching_enabled():
            return []
        
        matches = []
        smart_config = self.config.get_smart_matching_config()
        
        # Grupuj oferty po modelu
        by_model = {}
        for offer in offers_list:
            if offer.get('condition') in ['broken', 'parts', 'locked']:
                model = offer.get('model')
                if model:
                    if model not in by_model:
                        by_model[model] = []
                    by_model[model].append(offer)
        
        # Szukaj możliwych kombinacji
        for model, model_offers in by_model.items():
            if len(model_offers) < 2:
                continue
            
            pricing = self.config.get_pricing(model)
            if not pricing:
                continue
            
            # Sprawdź wszystkie pary
            for i, offer1 in enumerate(model_offers):
                for offer2 in model_offers[i+1:]:
                    # Oblicz koszt połączenia
                    combined_cost = offer1['buy_price'] + offer2['buy_price'] + pricing['repair_cost']
                    market_price = pricing['market_price']
                    max_combined = market_price * smart_config['max_combined_cost']
                    
                    if combined_cost <= max_combined:
                        potential_profit = market_price - combined_cost
                        
                        if potential_profit >= smart_config['min_profit_combined']:
                            # Określ typ kombinacji
                            damages1 = set(offer1.get('damages', []))
                            damages2 = set(offer2.get('damages', []))
                            
                            combination_type = "2x uszkodzone"
                            if 'ekran' in damages1 and 'obudowa' in damages2:
                                combination_type = "ekran + obudowa"
                            elif 'obudowa' in damages1 and 'ekran' in damages2:
                                combination_type = "ekran + obudowa"
                            elif offer1['condition'] == 'locked' or offer2['condition'] == 'locked':
                                combination_type = "icloud + uszkodzony"
                            
                            matches.append({
                                'model': model,
                                'offer1': offer1,
                                'offer2': offer2,
                                'combination_type': combination_type,
                                'combined_cost': combined_cost,
                                'market_price': market_price,
                                'potential_profit': potential_profit,
                                'profit_margin': (potential_profit / market_price * 100),
                                'recommendation': f"💡 Połącz 2 oferty! Zysk: {potential_profit}zł"
                            })
        
        # Sortuj po zyskowności
        matches.sort(key=lambda x: x['potential_profit'], reverse=True)
        
        return matches
