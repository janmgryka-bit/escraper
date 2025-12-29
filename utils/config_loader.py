import yaml
import os
from pathlib import Path

class ConfigLoader:
    def __init__(self, config_path='config.yaml'):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self):
        """Wczytaj konfigurację z pliku YAML"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Plik konfiguracyjny {self.config_path} nie istnieje!")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def reload(self):
        """Przeładuj konfigurację (bez restartowania bota)"""
        self.config = self._load_config()
    
    # Gettery dla łatwego dostępu
    
    def get_max_budget(self):
        return self.config['general']['max_budget']
    
    def get_check_interval(self):
        return (
            self.config['general']['check_interval_min'],
            self.config['general']['check_interval_max']
        )
    
    def get_enabled_models(self):
        return self.config['models']['enabled']
    
    def get_excluded_models(self):
        return self.config['models']['excluded']
    
    def get_enabled_conditions(self):
        """Zwraca listę włączonych stanów (uszkodzony, zablokowany, etc.)"""
        return [k for k, v in self.config['conditions'].items() if v]
    
    def get_pricing(self, model):
        """Pobierz cennik dla konkretnego modelu"""
        model_lower = model.lower().strip()
        return self.config['pricing'].get(model_lower)
    
    def is_model_enabled(self, model):
        """Sprawdź czy model jest na liście do wyszukiwania"""
        model_lower = model.lower().strip()
        
        # Sprawdź czy nie jest wykluczony
        for excluded in self.get_excluded_models():
            if excluded in model_lower:
                return False
        
        # Sprawdź czy jest włączony
        for enabled in self.get_enabled_models():
            if enabled in model_lower:
                return True
        
        return False
    
    def is_smart_matching_enabled(self):
        return self.config['smart_matching']['enabled']
    
    def get_smart_matching_config(self):
        return self.config['smart_matching']
    
    def is_ai_enabled(self):
        return self.config['ai']['enabled']
    
    def get_ai_config(self):
        return self.config['ai']
    
    def get_discord_config(self):
        return self.config['discord']
    
    def get_enabled_sources(self):
        """Zwraca listę włączonych źródeł (olx, facebook, etc.)"""
        return [k for k, v in self.config['sources'].items() if v]
    
    def save(self):
        """Zapisz aktualną konfigurację do pliku YAML"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
