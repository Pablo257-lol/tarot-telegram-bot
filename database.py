#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для работы с базой данных
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from telebot import types

logger = logging.getLogger(__name__)

class Database:
    """Класс для работы с SQLite базой данных"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        """Получение соединения с БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Инициализация базы данных"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Пользователи
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language_code TEXT,
                    is_bot BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP,
                    cards_drawn INTEGER DEFAULT 0,
                    readings_count INTEGER DEFAULT 0
                )
            ''')
            
            # Расклады
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    spread_type TEXT,
                    cards TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            conn.commit()
            logger.info("База данных инициализирована")
    
    def add_user(self, user: types.User):
        """Добавление пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO users 
                (user_id, username, first_name, last_name, language_code, is_bot, last_activity)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user.id,
                user.username,
                user.first_name,
                user.last_name,
                user.language_code,
                user.is_bot,
                datetime.now()
            ))
            conn.commit()
    
    def update_user_activity(self, user_id: int):
        """Обновление активности пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET last_activity = ?, 
                    cards_drawn = cards_drawn + 1,
                    readings_count = readings_count + 1
                WHERE user_id = ?
            ''', (datetime.now(), user_id))
            conn.commit()
    
    def save_reading(self, user_id: int, spread_type: str, cards: List[Dict]):
        """Сохранение расклада"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO readings (user_id, spread_type, cards)
                VALUES (?, ?, ?)
            ''', (
                user_id,
                spread_type,
                json.dumps(cards, ensure_ascii=False)
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_user_stats(self, user_id: int) -> Optional[Dict]:
        """Получение статистики пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM users WHERE user_id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_user_readings(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Получение раскладов пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM readings 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
            
            readings = []
            for row in cursor.fetchall():
                reading = dict(row)
                reading['cards'] = json.loads(reading['cards'])
                readings.append(reading)
            
            return readings
    
    def get_total_stats(self) -> Dict:
        """Получение общей статистики"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(cards_drawn) FROM users')
            total_cards = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT COUNT(*) FROM readings')
            total_readings = cursor.fetchone()[0]
            
            return {
                'total_users': total_users,
                'total_cards': total_cards,
                'total_readings': total_readings
            }
