import os
import json
import logging
from datetime import datetime

logger = logging.getLogger('escraper.ai')

class AIAnalyzer:
    def __init__(self, config_loader):
        self.config = config_loader
        self.ai_config = config_loader.get_ai_config()
        self.enabled = self.ai_config['enabled']
        
        if self.enabled:
            self._init_ai_client()
    
    def _init_ai_client(self):
        """Inicjalizuj klienta AI (Groq/OpenAI/Ollama)"""
        provider = self.ai_config['provider']
        
        if provider == 'groq':
            try:
                from groq import Groq
                api_key = os.getenv('GROQ_API_KEY')
                if not api_key:
                    logger.warning("⚠️ GROQ_API_KEY nie znaleziony w .env - AI wyłączone")
                    self.enabled = False
                    return
                self.client = Groq(api_key=api_key)
                logger.info("✅ AI (Groq) zainicjalizowane")
            except ImportError:
                logger.warning("⚠️ Biblioteka 'groq' nie zainstalowana - AI wyłączone")
                self.enabled = False
        
        elif provider == 'openai':
            try:
                from openai import OpenAI
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    logger.warning("⚠️ OPENAI_API_KEY nie znaleziony - AI wyłączone")
                    self.enabled = False
                    return
                self.client = OpenAI(api_key=api_key)
                logger.info("✅ AI (OpenAI) zainicjalizowane")
            except ImportError:
                logger.warning("⚠️ Biblioteka 'openai' nie zainstalowana - AI wyłączone")
                self.enabled = False
        
        else:
            logger.warning(f"⚠️ Nieznany provider AI: {provider} - AI wyłączone")
            self.enabled = False
    
    def analyze_offer(self, model, price, title, description="", image_urls=None):
        """
        Analizuje ofertę używając AI (tekst + opcjonalnie zdjęcia).
        
        Args:
            image_urls: Lista URL-i do zdjęć (opcjonalne)
        
        Returns:
            dict: {
                'is_good_deal': bool,
                'condition_score': int (1-10),
                'is_scam': bool,
                'estimated_profit': int,
                'worth_buying': bool,
                'ai_reasoning': str,
                'image_analysis': str (jeśli są zdjęcia)
            }
        """
        if not self.enabled:
            return None
        
        # Sprawdź czy analizować zdjęcia
        analyze_images = self.ai_config['checks'].get('analyze_images', False)
        if image_urls and analyze_images:
            return self._analyze_with_images(model, price, title, description, image_urls)
        else:
            return self._analyze_text_only(model, price, title, description)
    
    def _analyze_text_only(self, model, price, title, description):
        """Analiza tylko tekstu (bez zdjęć)"""
        if not self.enabled:
            return None
        
        try:
            # Przygotuj prompt
            prompt = self.ai_config['prompt_template'].format(
                model=model,
                price=price,
                description=f"{title}\n\n{description}"
            )
            
            # Wywołaj AI
            provider = self.ai_config['provider']
            model_name = self.ai_config['model']
            
            if provider == 'groq':
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "Jesteś ekspertem od iPhone'ów i handlu telefonami. Odpowiadaj TYLKO w formacie JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                ai_response = response.choices[0].message.content
            
            elif provider == 'openai':
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "Jesteś ekspertem od iPhone'ów i handlu telefonami. Odpowiadaj TYLKO w formacie JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                ai_response = response.choices[0].message.content
            
            # Parsuj odpowiedź JSON
            try:
                # Usuń markdown code blocks jeśli są
                if '```json' in ai_response:
                    ai_response = ai_response.split('```json')[1].split('```')[0]
                elif '```' in ai_response:
                    ai_response = ai_response.split('```')[1].split('```')[0]
                
                result = json.loads(ai_response.strip())
                
                # Znormalizuj odpowiedź
                return {
                    'is_good_deal': result.get('dobra_okazja', False) or result.get('is_good_deal', False),
                    'condition_score': result.get('stan', 5) or result.get('condition_score', 5),
                    'is_scam': result.get('oszustwo', False) or result.get('is_scam', False),
                    'estimated_profit': result.get('szacowany_zysk', 0) or result.get('estimated_profit', 0),
                    'worth_buying': result.get('warto_kupic', False) or result.get('worth_buying', False),
                    'ai_reasoning': result.get('uzasadnienie', '') or result.get('reasoning', '') or ai_response
                }
            
            except json.JSONDecodeError:
                logger.warning(f"⚠️ AI zwróciło nieprawidłowy JSON: {ai_response[:100]}")
                return {
                    'is_good_deal': False,
                    'condition_score': 5,
                    'is_scam': False,
                    'estimated_profit': 0,
                    'worth_buying': False,
                    'ai_reasoning': ai_response
                }
        
        except Exception as e:
            logger.error(f"❌ Błąd AI (text): {e}")
            return None
    
    def _analyze_with_images(self, model, price, title, description, image_urls):
        """
        Analiza z użyciem zdjęć (wymaga vision model).
        Groq: llama-3.2-90b-vision-preview
        OpenAI: gpt-4-vision-preview
        """
        if not self.enabled:
            return None
        
        try:
            provider = self.ai_config['provider']
            
            # Przygotuj prompt z informacją o zdjęciach
            prompt = f"""
Jesteś ekspertem od iPhone'ów. Przeanalizuj ofertę na podstawie opisu I ZDJĘĆ:

Model: {model}
Cena: {price} zł
Opis: {title}\n{description}

Przeanalizuj zdjęcia i oceń:
1. Rzeczywisty stan telefonu (1-10)
2. Widoczne uszkodzenia (ekran, obudowa, etc.)
3. Czy zdjęcia są autentyczne (nie stock photos)
4. Czy to może być oszustwo
5. Czy warto kupić

Odpowiedź w formacie JSON:
{{
  "condition_score": 1-10,
  "visible_damages": ["lista uszkodzeń"],
  "photos_authentic": true/false,
  "is_scam": true/false,
  "worth_buying": true/false,
  "image_analysis": "szczegółowa analiza zdjęć",
  "reasoning": "uzasadnienie"
}}
"""
            
            if provider == 'groq':
                # Groq vision model
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt}
                        ]
                    }
                ]
                
                # Dodaj zdjęcia (max 3)
                for img_url in image_urls[:3]:
                    messages[0]["content"].append({
                        "type": "image_url",
                        "image_url": {"url": img_url}
                    })
                
                response = self.client.chat.completions.create(
                    model="llama-3.2-90b-vision-preview",
                    messages=messages,
                    temperature=0.3,
                    max_tokens=800
                )
                ai_response = response.choices[0].message.content
            
            elif provider == 'openai':
                # OpenAI vision model
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt}
                        ]
                    }
                ]
                
                for img_url in image_urls[:3]:
                    messages[0]["content"].append({
                        "type": "image_url",
                        "image_url": {"url": img_url}
                    })
                
                response = self.client.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=messages,
                    max_tokens=800
                )
                ai_response = response.choices[0].message.content
            else:
                logger.warning(f"⚠️ Provider {provider} nie obsługuje vision")
                return self._analyze_text_only(model, price, title, description)
            
            # Parsuj JSON
            if '```json' in ai_response:
                ai_response = ai_response.split('```json')[1].split('```')[0]
            elif '```' in ai_response:
                ai_response = ai_response.split('```')[1].split('```')[0]
            
            result = json.loads(ai_response.strip())
            
            # Znormalizuj odpowiedź
            return {
                'is_good_deal': result.get('worth_buying', False),
                'condition_score': result.get('condition_score', 5),
                'is_scam': result.get('is_scam', False),
                'estimated_profit': 0,
                'worth_buying': result.get('worth_buying', False),
                'ai_reasoning': result.get('reasoning', ''),
                'image_analysis': result.get('image_analysis', ''),
                'visible_damages': result.get('visible_damages', []),
                'photos_authentic': result.get('photos_authentic', True)
            }
        
        except Exception as e:
            logger.error(f"❌ Błąd AI (vision): {e}")
            # Fallback do analizy tekstowej
            logger.info("⚠️ Fallback do analizy tekstowej")
            return self._analyze_text_only(model, price, title, description)
    
    def analyze_smart_match(self, offer1, offer2, combined_profit):
        """
        Analizuje czy połączenie dwóch ofert ma sens.
        """
        if not self.enabled:
            return None
        
        try:
            prompt = f"""
            Przeanalizuj połączenie dwóch ofert iPhone:
            
            Oferta 1:
            - Model: {offer1.get('model')}
            - Cena: {offer1.get('buy_price')} zł
            - Stan: {offer1.get('condition')}
            - Uszkodzenia: {', '.join(offer1.get('damages', []))}
            
            Oferta 2:
            - Model: {offer2.get('model')}
            - Cena: {offer2.get('buy_price')} zł
            - Stan: {offer2.get('condition')}
            - Uszkodzenia: {', '.join(offer2.get('damages', []))}
            
            Potencjalny zysk z połączenia: {combined_profit} zł
            
            Oceń:
            1. Czy to połączenie ma sens technicznie? (tak/nie)
            2. Jakie są ryzyka?
            3. Czy warto?
            
            Odpowiedź w formacie JSON: {{"makes_sense": bool, "risks": str, "worth_it": bool}}
            """
            
            provider = self.ai_config['provider']
            model_name = self.ai_config['model']
            
            if provider in ['groq', 'openai']:
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "Jesteś ekspertem od naprawy iPhone'ów. Odpowiadaj TYLKO w formacie JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=300
                )
                ai_response = response.choices[0].message.content
                
                # Parsuj JSON
                if '```json' in ai_response:
                    ai_response = ai_response.split('```json')[1].split('```')[0]
                elif '```' in ai_response:
                    ai_response = ai_response.split('```')[1].split('```')[0]
                
                return json.loads(ai_response.strip())
        
        except Exception as e:
            logger.error(f"❌ Błąd AI (smart match): {e}")
            return None
