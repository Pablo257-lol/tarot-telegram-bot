#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Классы для работы с картами Таро
"""

import json
import random
from enum import Enum
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional, Dict
from pathlib import Path

class CardType(Enum):
    """Типы карт Таро"""
    MAJOR = "Старшие Арканы"
    CUPS = "Кубки"
    SWORDS = "Мечи"
    WANDS = "Жезлы"
    PENTACLES = "Пентакли"

@dataclass
class TarotCard:
    """Класс карты Таро"""
    name: str
    upright: str
    reversed: str
    card_type: CardType
    number: Optional[int] = None
    keywords: List[str] = None
    element: str = ""
    astro: str = ""
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
    
    def get_meaning(self, is_reversed: bool = False) -> str:
        """Получение значения карты"""
        return self.reversed if is_reversed else self.upright
    
    def get_short_meaning(self, is_reversed: bool = False, max_length: int = 100) -> str:
        """Краткое значение"""
        meaning = self.get_meaning(is_reversed)
        return meaning[:max_length] + "..." if len(meaning) > max_length else meaning
    
    def get_description(self, is_reversed: bool = False) -> str:
        """Полное описание карты"""
        position = "🔻 Перевернутая" if is_reversed else "🔺 Прямая"
        
        description = f"🎴 *{self.name}*\n"
        description += f"📊 *Тип:* {self.card_type.value}\n"
        description += f"⚖️ *Положение:* {position}\n\n"
        description += f"📖 *Значение:*\n{self.get_meaning(is_reversed)}\n\n"
        
        if self.keywords:
            description += f"🏷️ *Ключевые слова:* {', '.join(self.keywords)}\n"
        
        if self.element:
            description += f"🌿 *Стихия:* {self.element}\n"
        
        if self.astro:
            description += f"⭐ *Астрология:* {self.astro}\n"
        
        return description
    
    def get_short_description(self, is_reversed: bool = False) -> str:
        """Краткое описание"""
        return f"{self.name} ({'🔻' if is_reversed else '🔺'}) - {self.get_short_meaning(is_reversed)}"
    
    def to_dict(self, is_reversed: bool = False) -> Dict:
        """Конвертация в словарь"""
        return {
            'name': self.name,
            'type': self.card_type.value,
            'position': 'reversed' if is_reversed else 'upright',
            'meaning': self.get_meaning(is_reversed),
            'short_meaning': self.get_short_meaning(is_reversed)
        }

class TarotDeck:
    """Колода карт Таро"""
    
    def __init__(self):
        self.cards: List[TarotCard] = []
        self.load_deck()
    
    def load_deck(self):
        """Загрузка колоды"""
        # Попробуем загрузить из файла
        deck_file = Path(__file__).parent / "data" / "tarot_deck.json"
        
        if deck_file.exists():
            try:
                with open(deck_file, 'r', encoding='utf-8') as f:
                    cards_data = json.load(f)
                
                for card_data in cards_data:
                    card_data['card_type'] = CardType(card_data['card_type'])
                    self.cards.append(TarotCard(**card_data))
                
                print(f"✅ Загружено {len(self.cards)} карт из файла")
                return
            except Exception as e:
                print(f"❌ Ошибка загрузки из файла: {e}")
        
        # Иначе создаем базовую колоду
        self._create_basic_deck()
        print(f"✅ Создана базовая колода из {len(self.cards)} карт")
    
    def _create_basic_deck(self):
        """Создание базовой колоды"""
        # Старшие Арканы
        major_arcana = [
            TarotCard("0. Шут", "Начало, свобода, невинность", "Безрассудство, риск", CardType.MAJOR, 0,
                     ["начало", "свобода"], "Воздух"),
            TarotCard("I. Маг", "Воля, мастерство, концентрация", "Манипуляции, слабость", CardType.MAJOR, 1,
                     ["воля", "мастерство"], "Меркурий"),
            TarotCard("II. Верховная Жрица", "Интуиция, тайное знание", "Скрытые мотивы", CardType.MAJOR, 2,
                     ["интуиция", "тайны"], "Луна"),
            TarotCard("III. Императрица", "Изобилие, творчество", "Зависимость", CardType.MAJOR, 3,
                     ["изобилие", "творчество"], "Венера"),
            TarotCard("IV. Император", "Власть, структура", "Тирания", CardType.MAJOR, 4,
                     ["власть", "структура"], "Марс"),
        ]
        
        # Масть Кубки
        cups_cards = [
            TarotCard("Туз Кубков", "Новые чувства, любовь", "Эмоциональная пустота", CardType.CUPS, 1,
                     ["любовь", "чувства"], "Вода"),
            TarotCard("Двойка Кубков", "Единство, гармония", "Разрыв", CardType.CUPS, 2,
                     ["партнерство", "гармония"], "Вода"),
        ]
        
        # Масть Мечи
        swords_cards = [
            TarotCard("Туз Мечей", "Ясность, правда", "Путаница", CardType.SWORDS, 1,
                     ["ясность", "правда"], "Воздух"),
            TarotCard("Двойка Мечей", "Выбор, баланс", "Неуверенность", CardType.SWORDS, 2,
                     ["выбор", "баланс"], "Воздух"),
        ]
        
        # Масть Жезлы
        wands_cards = [
            TarotCard("Туз Жезлов", "Вдохновение, энергия", "Задержки", CardType.W
