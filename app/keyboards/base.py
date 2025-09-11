"""Base keyboard builder."""

from typing import List, Dict, Any, Optional
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class BaseKeyboardBuilder:
    """Base class for keyboard builders."""
    
    def __init__(self):
        self.buttons: List[List[InlineKeyboardButton]] = []
    
    def add_button(
        self,
        text: str,
        callback_data: str = None,
        url: str = None,
        switch_inline_query: str = None,
        switch_inline_query_current_chat: str = None
    ) -> 'BaseKeyboardBuilder':
        """Add a button to a new row."""
        button = InlineKeyboardButton(
            text=text,
            callback_data=callback_data,
            url=url,
            switch_inline_query=switch_inline_query,
            switch_inline_query_current_chat=switch_inline_query_current_chat
        )
        self.buttons.append([button])
        return self
    
    def add_buttons_row(self, buttons: List[Dict[str, Any]]) -> 'BaseKeyboardBuilder':
        """Add multiple buttons in the same row."""
        row = []
        for btn_data in buttons:
            button = InlineKeyboardButton(**btn_data)
            row.append(button)
        self.buttons.append(row)
        return self
    
    def add_back_button(self, callback_data: str = "back", text: str = "⬅️ Back") -> 'BaseKeyboardBuilder':
        """Add a back button."""
        return self.add_button(text, callback_data)
    
    def add_cancel_button(self, callback_data: str = "cancel", text: str = "❌ Cancel") -> 'BaseKeyboardBuilder':
        """Add a cancel button."""
        return self.add_button(text, callback_data)
    
    def add_pagination(
        self,
        current_page: int,
        total_pages: int,
        callback_prefix: str = "page"
    ) -> 'BaseKeyboardBuilder':
        """Add pagination buttons."""
        if total_pages <= 1:
            return self
        
        row = []
        
        # Previous button
        if current_page > 1:
            row.append(InlineKeyboardButton(
                "⬅️",
                callback_data=f"{callback_prefix}:{current_page - 1}"
            ))
        
        # Page indicator
        row.append(InlineKeyboardButton(
            f"{current_page}/{total_pages}",
            callback_data="current_page"
        ))
        
        # Next button
        if current_page < total_pages:
            row.append(InlineKeyboardButton(
                "➡️",
                callback_data=f"{callback_prefix}:{current_page + 1}"
            ))
        
        self.buttons.append(row)
        return self
    
    def build(self) -> InlineKeyboardMarkup:
        """Build the keyboard markup."""
        return InlineKeyboardMarkup(self.buttons)
    
    def clear(self) -> 'BaseKeyboardBuilder':
        """Clear all buttons."""
        self.buttons.clear()
        return self








