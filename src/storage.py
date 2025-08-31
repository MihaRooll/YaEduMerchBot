import json
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class JSONStorage:
    """Класс для работы с JSON файлами данных"""
    
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
            "settings.json": {},
            "chat_messages.json": {},
            "audit_log.json": {}
        }
        
        for filename, default_data in files.items():
            filepath = os.path.join(self.data_dir, filename)
            if not os.path.exists(filepath):
                self._write_file(filename, default_data)
                logger.info(f"Создан файл: {filename}")
    
    def _get_filepath(self, filename: str) -> str:
        """Получение полного пути к файлу"""
        return os.path.join(self.data_dir, filename)
    
    def _read_file(self, filename: str) -> Dict[str, Any]:
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
    
    def _write_file(self, filename: str, data: Dict[str, Any]):
        """Запись в JSON файл"""
        try:
            filepath = self._get_filepath(filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка записи в файл {filename}: {e}")
            raise
    
    def get_all(self, filename: str) -> Dict[str, Any]:
        """Получить все данные из файла"""
        return self._read_file(filename)
    
    def get(self, filename: str, key: str) -> Optional[Any]:
        """Получить значение по ключу"""
        data = self._read_file(filename)
        return data.get(key)
    
    def set(self, filename: str, key: str, value: Any):
        """Установить значение по ключу"""
        data = self._read_file(filename)
        data[key] = value
        self._write_file(filename, data)
    
    def delete(self, filename: str, key: str) -> bool:
        """Удалить значение по ключу"""
        data = self._read_file(filename)
        if key in data:
            del data[key]
            self._write_file(filename, data)
            return True
        return False
    
    def exists(self, filename: str, key: str) -> bool:
        """Проверить существование ключа"""
        data = self._read_file(filename)
        return key in data
    
    def get_keys(self, filename: str) -> List[str]:
        """Получить список всех ключей"""
        data = self._read_file(filename)
        return list(data.keys())
    
    def count(self, filename: str) -> int:
        """Получить количество записей"""
        data = self._read_file(filename)
        return len(data)


# Глобальный экземпляр хранилища
storage = JSONStorage()
