#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 Основной файл Telegram бота для гадания на Таро
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Добавляем текущую директорию в путь для импортов
sys.path.append(str(Path(__file__).parent))

from config import Config
from database import Database
from tarot_deck import TarotDeck, TarotCard, CardType
from tarot_spreads import TarotSpreads

import telebot
from telebot import types
from telebot.types import BotCommand, BotCommandScopeChat

# Настройка логирования
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format=Config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(Config.LOGS_DIR / "tarot_bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TarotBot:
    """Основной класс бота"""
    
    def __init__(self, token: str):
        self.token = token
        self.bot = telebot.TeleBot(token, parse_mode=Config.PARSE_MODE)
        self.db = Database(str(Config.DB_FILE))
        self.deck = TarotDeck()
        self.spreads = TarotSpreads()
        self.is_running = False
        
        # Загрузка конфигурации
        self.load_config()
        
        # Настройка обработчиков
        self.setup_handlers()
        self.setup_menu_commands()
        
        logger.info(f"Бот инициализирован")
    
    def load_config(self):
        """Загрузка конфигурации"""
        try:
            if Config.CONFIG_FILE.exists():
                with open(Config.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    Config.TOKEN = config_data.get('token', '')
                    Config.ADMIN_ID = config_data.get('admin_id', 0)
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}")
    
    def setup_menu_commands(self):
        """Настройка команд меню бота"""
        try:
            commands = [
                BotCommand("start", "🎴 Начало работы"),
                BotCommand("card", "🎴 Быстрая карта"),
                BotCommand("day", "✨ Карта дня"),
                BotCommand("three", "🔮 3 карты"),
                BotCommand("love", "💖 Любовь"),
                BotCommand("work", "💼 Работа"),
                BotCommand("money", "💰 Финансы"),
                BotCommand("health", "🏥 Здоровье"),
                BotCommand("quick", "⚡ Все команды"),
                BotCommand("help", "❓ Помощь")
            ]
            
            self.bot.set_my_commands(commands)
            
            # Команды для админа
            if Config.ADMIN_ID:
                admin_commands = commands + [
                    BotCommand("admin_stats", "📈 Статистика"),
                    BotCommand("broadcast", "📢 Рассылка")
                ]
                admin_scope = BotCommandScopeChat(Config.ADMIN_ID)
                self.bot.set_my_commands(admin_commands, scope=admin_scope)
            
            logger.info("Команды меню настроены")
        except Exception as e:
            logger.error(f"Ошибка настройки команд: {e}")
    
    def setup_handlers(self):
        """Настройка обработчиков команд"""
        
        @self.bot.message_handler(commands=['start', 'help'])
        def handle_start(message):
            """Обработчик команды /start"""
            user = message.from_user
            self.db.add_user(user)
            
            welcome_text = self.get_welcome_text(user.first_name, message.chat.type)
            self.bot.send_message(message.chat.id, welcome_text)
            
            logger.info(f"Пользователь {user.id} начал работу")
        
        @self.bot.message_handler(commands=['card'])
        def handle_card(message):
            """Быстрая карта"""
            self.handle_quick_spread(message, "quick_card")
        
        @self.bot.message_handler(commands=['day'])
        def handle_day(message):
            """Карта дня"""
            self.handle_quick_spread(message, "daily")
        
        @self.bot.message_handler(commands=['three'])
        def handle_three(message):
            """3 карты"""
            self.handle_quick_spread(message, "three_cards")
        
        @self.bot.message_handler(commands=['love'])
        def handle_love(message):
            """Расклад на любовь"""
            self.handle_quick_spread(message, "love_spread")
        
        @self.bot.message_handler(commands=['work'])
        def handle_work(message):
            """Расклад на работу"""
            self.handle_quick_spread(message, "work_spread")
        
        @self.bot.message_handler(commands=['money'])
        def handle_money(message):
            """Финансовый расклад"""
            self.handle_quick_spread(message, "money_spread")
        
        @self.bot.message_handler(commands=['health'])
        def handle_health(message):
            """Расклад на здоровье"""
            self.handle_quick_spread(message, "health_spread")
        
        @self.bot.message_handler(commands=['quick'])
        def handle_quick(message):
            """Все быстрые команды"""
            response = self.get_all_commands()
            self.bot.send_message(message.chat.id, response)
        
        @self.bot.message_handler(commands=['stats'])
        def handle_stats(message):
            """Статистика пользователя"""
            user = message.from_user
            stats = self.db.get_user_stats(user.id)
            
            if stats:
                response = f"📊 *Статистика*\n\n" \
                          f"• Карт вытянуто: {stats.get('cards_drawn', 0)}\n" \
                          f"• Раскладов: {stats.get('readings_count', 0)}\n" \
                          f"• С вами с: {stats.get('created_at', '')[:10]}"
            else:
                response = "📊 У вас пока нет статистики"
            
            self.bot.send_message(message.chat.id, response)
    
    def handle_quick_spread(self, message, spread_type: str):
        """Обработка быстрого расклада"""
        user = message.from_user
        spread_info = self.spreads.get_spread_info(spread_type)
        
        if not spread_info:
            self.bot.send_message(message.chat.id, "❌ Расклад не найден")
            return
        
        # Получаем карты для расклада
        cards_data = self.deck.draw_cards(spread_info['cards'])
        
        # Форматируем ответ
        response = self.format_spread_response(spread_info, cards_data, user.first_name)
        
        # Сохраняем в базу
        self.db.save_reading(user.id, spread_type, cards_data)
        self.db.update_user_activity(user.id)
        
        # Отправляем ответ
        self.bot.send_message(message.chat.id, response, parse_mode="Markdown")
        
        logger.info(f"Расклад {spread_type} для пользователя {user.id}")
    
    def format_spread_response(self, spread_info: dict, cards_data: list, user_name: str) -> str:
        """Форматирование ответа для расклада"""
        response = f"✨ *{spread_info['name']} для {user_name}* ✨\n\n"
        
        if spread_info['type'] == 'daily':
            card, is_reversed = cards_data[0]
            response += card.get_description(is_reversed)
            response += "\n\n🌅 *Совет на день:* Прислушайтесь к интуиции!"
        
        elif spread_info['type'] == 'three_cards':
            positions = spread_info.get('positions', ['Прошлое', 'Настоящее', 'Будущее'])
            response += f"*{spread_info['description']}*\n\n"
            
            for i, ((card, is_reversed), position) in enumerate(zip(cards_data, positions), 1):
                response += f"*{i}. {position}:*\n"
                response += f"{card.get_description(is_reversed)}\n\n"
        
        else:
            positions = spread_info.get('positions', [])
            response += f"*{spread_info['description']}*\n\n"
            
            for i, (card, is_reversed) in enumerate(cards_data, 1):
                position = positions[i-1] if i <= len(positions) else f"Карта {i}"
                response += f"*{i}. {position}:*\n"
                response += f"{card.get_short_description(is_reversed)}\n\n"
        
        return response
    
    def get_welcome_text(self, user_name: str, chat_type: str) -> str:
        """Получить приветственный текст"""
        if chat_type == 'private':
            return (
                f"✨ *Добро пожаловать, {user_name}!* ✨\n\n"
                f"Я — *бот для гадания на Таро* 🎴\n\n"
                f"*⚡ Быстрые команды:*\n"
                f"• `/card` - Быстрая карта\n"
                f"• `/day` - Карта дня\n"
                f"• `/three` - 3 карты\n"
                f"• `/love` - Любовь\n"
                f"• `/work` - Работа\n"
                f"• `/money` - Финансы\n"
                f"• `/health` - Здоровье\n"
                f"• `/quick` - Все команды\n\n"
                f"🎴 *Выберите команду из меню!*"
            )
        else:
            return (
                f"✨ *Таро-бот в вашей группе!* ✨\n\n"
                f"Используйте команды:\n"
                f"• `/card` - Быстрая карта\n"
                f"• `/day` - Карта дня\n"
                f"• `/three` - 3 карты\n\n"
                f"💡 *Пример:* `/card`"
            )
    
    def get_all_commands(self) -> str:
        """Получить список всех команд"""
        commands = [
            "🎴 *Доступные команды:*\n\n",
            "• /card - Быстрая карта",
            "• /day - Карта дня",
            "• /three - 3 карты (Прошлое-Настоящее-Будущее)",
            "• /love - Расклад на любовь",
            "• /work - Расклад на работу",
            "• /money - Финансовый расклад",
            "• /health - Расклад на здоровье",
            "• /yesno - Да/Нет расклад",
            "• /advice - Карта совета",
            "• /future - Расклад на будущее\n\n",
            "📊 /stats - Ваша статистика",
            "⚡ /quick - Повторно показать команды",
            "❓ /help - Помощь"
        ]
        
        return "\n".join(commands)
    
    def start(self):
        """Запуск бота"""
        if self.is_running:
            logger.warning("Бот уже запущен")
            return False
        
        self.is_running = True
        
        try:
            # Проверка токена
            bot_info = self.bot.get_me()
            logger.info(f"Бот @{bot_info.username} успешно запущен")
            
            # Запуск polling
            import threading
            polling_thread = threading.Thread(target=self._run_polling, daemon=True)
            polling_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
            self.is_running = False
            return False
    
    def _run_polling(self):
        """Запуск polling в отдельном потоке"""
        try:
            while self.is_running:
                try:
                    self.bot.polling(
                        none_stop=True,
                        interval=Config.POLLING_INTERVAL,
                        timeout=Config.POLLING_TIMEOUT
                    )
                except Exception as e:
                    logger.error(f"Ошибка в polling: {e}")
                    import time
                    time.sleep(5)
        except KeyboardInterrupt:
            logger.info("Бот остановлен пользователем")
        finally:
            self.is_running = False
    
    def stop(self):
        """Остановка бота"""
        if not self.is_running:
            logger.warning("Бот уже остановлен")
            return
        
        self.is_running = False
        try:
            self.bot.stop_polling()
            logger.info("Бот остановлен")
        except Exception as e:
            logger.error(f"Ошибка при остановке бота: {e}")

def setup_config():
    """Настройка конфигурации"""
    print("=" * 60)
    print("🛠️  НАСТРОЙКА ТАРО БОТА")
    print("=" * 60)
    print()
    
    token = input("Введите токен бота от @BotFather: ").strip()
    if not token:
        print("❌ Токен не может быть пустым")
        return False
    
    admin_id = input("Введите ваш Telegram ID (для админ-прав, опционально): ").strip()
    admin_id = int(admin_id) if admin_id.isdigit() else 0
    
    config_data = {
        'token': token,
        'admin_id': admin_id
    }
    
    # Создаем директории
    Config.setup_dirs()
    
    # Сохраняем конфигурацию
    try:
        with open(Config.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Конфигурация сохранена в {Config.CONFIG_FILE}")
        
        # Тестируем бота
        try:
            bot = TarotBot(token)
            bot_info = bot.bot.get_me()
            print(f"✅ Бот подключен: @{bot_info.username}")
            print(f"🔗 Ссылка: https://t.me/{bot_info.username}")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка сохранения конфигурации: {e}")
        return False

def main():
    """Основная функция запуска"""
    parser = argparse.ArgumentParser(description='Telegram бот для гадания на Таро')
    parser.add_argument('--setup', action='store_true', help='Настройка бота')
    parser.add_argument('--token', help='Токен бота')
    parser.add_argument('--admin-id', type=int, help='ID администратора')
    
    args = parser.parse_args()
    
    # Настройка директорий
    Config.setup_dirs()
    
    if args.setup:
        setup_config()
        return
    
    # Загрузка конфигурации
    if not Config.CONFIG_FILE.exists():
        print("❌ Конфигурационный файл не найден")
        print("💡 Используйте: python tarot_bot.py --setup")
        return
    
    try:
        with open(Config.CONFIG_FILE, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        Config.TOKEN = config_data.get('token', '')
        Config.ADMIN_ID = config_data.get('admin_id', 0)
        
        if not Config.TOKEN:
            print("❌ Токен не найден в конфигурации")
            print("💡 Используйте: python tarot_bot.py --setup")
            return
        
    except Exception as e:
        print(f"❌ Ошибка загрузки конфигурации: {e}")
        return
    
    # Запуск бота
    print("=" * 60)
    print("🤖 ЗАПУСК ТАРО БОТА")
    print("=" * 60)
    print()
    
    bot = TarotBot(Config.TOKEN)
    
    if bot.start():
        print("✅ Бот успешно запущен!")
        print()
        print("📱 Команды в Telegram:")
        print("• /start - Начало работы")
        print("• /card - Быстрая карта")
        print("• /day - Карта дня")
        print("• /three - 3 карты")
        print("• /quick - Все команды")
        print()
        print("=" * 60)
        print("🛑 Для остановки нажмите Ctrl+C")
        print("=" * 60)
        
        try:
            while bot.is_running:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Останавливаю бота...")
            bot.stop()
        
        print("👋 Бот остановлен")
    else:
        print("❌ Не удалось запустить бота")

if __name__ == "__main__":
    main()
