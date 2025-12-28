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
    
    def analyze_offer(self, model, price, title, description=""):
        """
        Analizuje ofertę używając AI.
        
        Returns:
            dict: {
                'is_good_deal': bool,
                'condition_score': int (1-10),
                'is_scam': bool,
                'estimated_profit': int,
                'worth_buying': bool,
                'ai_reasoning': str
            }
        """
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
            logger.error(f"❌ Błąd AI: {e}")
            return None
    
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
