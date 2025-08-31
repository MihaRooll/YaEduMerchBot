#!/usr/bin/env python3
"""
Скрипт для инициализации данных системы
"""

import sys
import os
import json
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleStorage:
    """Простое хранилище для инициализации"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self._ensure_data_dir()
        self._init_data_files()
    
    def _ensure_data_dir(self):
        """Создание папки для данных если не существует"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            logger.info(f"Создана папка данных: {self.data_dir}")
    
    def _init_data_files(self):
        """Инициализация JSON файлов с базовой структурой"""
        files = {
            "users.json": {},
            "chats.json": {},
            "inventory.json": {},
            "orders.json": {},
            "settings.json": {}
        }
        
        for filename, default_data in files.items():
            filepath = os.path.join(self.data_dir, filename)
            if not os.path.exists(filepath):
                self._write_file(filename, default_data)
                logger.info(f"Создан файл: {filename}")
    
    def _get_filepath(self, filename: str) -> str:
        """Получение полного пути к файлу"""
        return os.path.join(self.data_dir, filename)
    
    def _read_file(self, filename: str) -> dict:
        """Чтение JSON файла"""
        try:
            filepath = self._get_filepath(filename)
            if not os.path.exists(filepath):
                return {}
            
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка чтения файла {filename}: {e}")
            return {}
    
    def _write_file(self, filename: str, data: dict):
        """Запись в JSON файл"""
        try:
            filepath = self._get_filepath(filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка записи в файл {filename}: {e}")
            raise
    
    def set(self, filename: str, key: str, value):
        """Установить значение по ключу"""
        data = self._read_file(filename)
        data[key] = value
        self._write_file(filename, data)
    
    def count(self, filename: str) -> int:
        """Получить количество записей"""
        data = self._read_file(filename)
        return len(data)


def init_system():
    """Инициализация системы"""
    logger.info("Начинаем инициализацию системы...")
    
    # Инициализируем хранилище
    storage = SimpleStorage()
    logger.info("Инициализация хранилища завершена")
    
    # Создаем главного админа
    logger.info("Создание главного админа...")
    main_admin_data = {
        "username": "main_admin",
        "first_name": "Главный Администратор",
        "role": "admin",
        "added_by": "system",
        "added_at": datetime.now().isoformat(),
        "is_active": True
    }
    storage.set("users.json", "445075408", main_admin_data)
    logger.info("Главный админ создан")
    
    # Добавим тестовые чаты
    logger.info("Добавление тестовых чатов...")
    test_chats = {
        "-1001234567890": {
            "title": "Общий чат мерча",
            "prefix": "A",
            "is_common": True,
            "is_active": True
        },
        "-1001234567891": {
            "title": "Чат заказов",
            "prefix": "B", 
            "is_common": False,
            "is_active": True
        }
    }
    
    for chat_id, chat_data in test_chats.items():
        storage.set("chats.json", chat_id, chat_data)
        logger.info(f"Добавлен чат: {chat_data['title']}")
    
    # Добавим тестовый инвентарь
    logger.info("Добавление тестового инвентаря...")
    test_inventory = {
        "products": {
            "longsleeve_white": {
                "name": "Лонгслив белый",
                "type": "longsleeve",
                "base_color": "white",
                "sizes": {
                    "S": {"qty_total": 10, "qty_reserved": 0},
                    "M": {"qty_total": 15, "qty_reserved": 0},
                    "L": {"qty_total": 12, "qty_reserved": 0}
                },
                "active": True
            }
        },
        "sizes": {
            "S": {"colors": {"white": {"qty_total": 10, "qty_reserved": 0}}},
            "M": {"colors": {"white": {"qty_total": 15, "qty_reserved": 0}}},
            "L": {"colors": {"white": {"qty_total": 12, "qty_reserved": 0}}}
        }
    }
    
    storage.set("inventory.json", "data", test_inventory)
    logger.info("Инвентарь инициализирован")
    
    # Добавим базовые настройки
    logger.info("Добавление базовых настроек...")
    base_settings = {
        "system_name": "YaEduMerchBot",
        "version": "1.0.0",
        "order_prefix": "ORD",
        "max_orders_per_user": 1
    }
    
    for key, value in base_settings.items():
        storage.set("settings.json", key, value)
        logger.info(f"Добавлена настройка: {key} = {value}")
    
    logger.info("Инициализация системы завершена успешно!")
    
    # Покажем статистику
    logger.info("Статистика системы:")
    logger.info(f"Пользователей: {storage.count('users.json')}")
    logger.info(f"Чатов: {storage.count('chats.json')}")
    logger.info(f"Товаров: {storage.count('inventory.json')}")
    logger.info(f"Настроек: {storage.count('settings.json')}")


if __name__ == "__main__":
    try:
        init_system()
    except Exception as e:
        logger.error(f"Ошибка инициализации: {e}")
        sys.exit(1)
