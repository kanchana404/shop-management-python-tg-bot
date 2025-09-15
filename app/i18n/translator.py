"""Translation system."""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from app.models import LanguageCode

class Translator:
    """Translation manager."""
    
    def __init__(self):
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.load_translations()
    
    def load_translations(self):
        """Load all translation files."""
        i18n_dir = Path(__file__).parent
        
        for lang_file in i18n_dir.glob("*.yml"):
            lang_code = lang_file.stem
            
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = yaml.safe_load(f)
            except Exception as e:
                print(f"Error loading translation file {lang_file}: {e}")
    
    def get_text(
        self,
        key: str,
        language: str = "en",
        fallback_language: str = "en",
        **kwargs
    ) -> str:
        """
        Get translated text by key.
        
        Args:
            key: Translation key (e.g., 'start.welcome')
            language: Target language code
            fallback_language: Fallback language if translation not found
            **kwargs: Variables for string formatting
        """
        # Try to get translation in requested language
        text = self._get_nested_value(self.translations.get(language, {}), key)
        
        # Fallback to fallback language if not found
        if text is None and language != fallback_language:
            text = self._get_nested_value(self.translations.get(fallback_language, {}), key)
        
        # Final fallback to key itself
        if text is None:
            text = key
        
        # Format with variables if provided
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError):
                pass  # Return unformatted text if formatting fails
        
        return text
    
    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Optional[str]:
        """Get value from nested dictionary using dot notation."""
        keys = key.split('.')
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        
        return current if isinstance(current, str) else None
    
    def get_available_languages(self) -> Dict[str, str]:
        """Get available language codes and names."""
        return {
            LanguageCode.ENGLISH.value: "🇺🇸 English",
            LanguageCode.SERBIAN.value: "🇷🇸 Serbian",
            LanguageCode.RUSSIAN.value: "🇷🇺 Russian",
        }
    
    def is_language_supported(self, language_code: str) -> bool:
        """Check if language is supported."""
        return language_code in self.translations


# Global translator instance
translator = Translator()


def _(key: str, language: str = "en", **kwargs) -> str:
    """Shorthand function for getting translations."""
    return translator.get_text(key, language, **kwargs)


def get_user_language(user) -> str:
    """Get user's language code, fallback to English."""
    if user and hasattr(user, 'language_code') and user.language_code:
        return user.language_code
    return LanguageCode.ENGLISH.value











