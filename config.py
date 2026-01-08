#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Конфигурация приложения
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """Конфигурационные параметры"""
    
    # Пути
    BASE_DIR: Path = Path(__file__).parent.absolute()
    DATA_DIR: Path = BASE_DIR / "data"
    LOGS_DIR: Path = BASE_DIR / "logs"
    IMAGES_DIR: Path = BASE_DIR / "images"
    
    # Файлы
    DB_FILE: Path = DATA_DIR / "tarot_bot.db"
    CONFIG_FILE: Path = DATA_DIR / "config.json"
    QUICK_COMMANDS_FILE: Path = DATA_DIR / "quick_commands.json"
    
    # Настройки бота
    TOKEN: str = ""
    ADMIN_ID: int = 0
    
    # Настройки базы данных
    DB_SCHEMA_VERSION: int = 1
    
    # Настройки логирования
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Настройки бота
    PARSE_MODE: str = "Markdown"
    POLLING_TIMEOUT: int = 20
    POLLING_INTERVAL: int = 0
    
    @classmethod
    def setup_dirs(cls):
        """Создание необходимых директорий"""
        for directory in [cls.DATA_DIR, cls.LOGS_DIR, cls.IMAGES_DIR]:
            directory.mkdir(exist_ok=True)
    
    @classmethod
    def validate_config(cls) -> bool:
        """Проверка конфигурации"""
        if not cls.TOKEN:
            raise ValueError("Токен бота не установлен. Используйте --setup для настройки.")
        return True
