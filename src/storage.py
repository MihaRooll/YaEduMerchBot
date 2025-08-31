import json
import os
import logging
import tempfile
import shutil
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)


def load_json(path: str, default: Any = None) -> Any:
    """Загрузка JSON файла с дефолтным значением"""
    try:
        if not os.path.exists(path):
            return default
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка чтения файла {path}: {e}")
        return default


def save_json_atomic(path: str, data: Any) -> bool:
    """Атомарное сохранение JSON через временный файл"""
    try:
        # Создаем временный файл
        temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(path), suffix='.tmp')
        os.close(temp_fd)
        
        # Записываем во временный файл
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Атомарно переименовываем
        shutil.move(temp_path, path)
        return True
    except Exception as e:
        logger.error(f"Ошибка атомарной записи в файл {path}: {e}")
        # Удаляем временный файл если он остался
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        return False


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
            "meta.json": {"next_order_id": 1},
            "users.json": {},
            "chats.json": [],
            "inventory.json": {
                "sizes": {
                    "S": {"colors": {"_": {"qty_total": 10, "qty_reserved": 0}}},
                    "M": {"colors": {"_": {"qty_total": 10, "qty_reserved": 0}}},
                    "L": {"colors": {"_": {"qty_total": 10, "qty_reserved": 0}}},
                    "XL": {"colors": {"_": {"qty_total": 10, "qty_reserved": 0}}}
                }
            },
            "orders.json": []
        }
        
        for filename, default_data in files.items():
            filepath = os.path.join(self.data_dir, filename)
            if not os.path.exists(filepath):
                save_json_atomic(filepath, default_data)
                logger.info(f"Создан файл: {filename}")
    
    def _get_filepath(self, filename: str) -> str:
        """Получение полного пути к файлу"""
        return os.path.join(self.data_dir, filename)
    
    def _read_file(self, filename: str) -> Any:
        """Чтение JSON файла"""
        filepath = self._get_filepath(filename)
        return load_json(filepath, {} if filename == "users.json" else [])
    
    def _write_file(self, filename: str, data: Any) -> bool:
        """Запись в JSON файл"""
        filepath = self._get_filepath(filename)
        return save_json_atomic(filepath, data)
    
    def next_order_id(self) -> int:
        """Получение следующего ID заказа"""
        meta_path = self._get_filepath("meta.json")
        orders_path = self._get_filepath("orders.json")
        
        # Пробуем взять из meta
        meta = load_json(meta_path, {"next_order_id": 1})
        next_id = meta.get("next_order_id", 1)
        
        # Если нет в meta, вычисляем из orders
        if next_id == 1:
            orders = load_json(orders_path, [])
            if orders:
                max_id = max(order.get("id", 0) for order in orders)
                next_id = max_id + 1
        
        # Обновляем meta
        meta["next_order_id"] = next_id + 1
        save_json_atomic(meta_path, meta)
        
        return next_id
    
    # Утилиты для пользователей
    def get_or_create_user(self, tg_user) -> Dict[str, Any]:
        """Получить или создать пользователя"""
        users = self._read_file("users.json")
        tg_id = str(tg_user.id)
        
        if tg_id not in users:
            users[tg_id] = {
                "username": tg_user.username or "",
                "first_name": tg_user.first_name or "",
                "last_name": tg_user.last_name or "",
                "total_orders": 0,
                "created_at": datetime.now().isoformat()
            }
            self._write_file("users.json", users)
        
        return users[tg_id]
    
    def inc_total_orders(self, tg_id: Union[str, int]) -> int:
        """Увеличить счетчик заказов пользователя"""
        users = self._read_file("users.json")
        tg_id_str = str(tg_id)
        
        if tg_id_str in users:
            users[tg_id_str]["total_orders"] = users[tg_id_str].get("total_orders", 0) + 1
            self._write_file("users.json", users)
            return users[tg_id_str]["total_orders"]
        return 0
    
    # Утилиты для чатов
    def list_active_chats(self) -> List[Dict[str, Any]]:
        """Список активных чатов"""
        chats = self._read_file("chats.json")
        return [chat for chat in chats if chat.get("active", True)]
    
    def add_chat(self, chat_data: Dict[str, Any]) -> bool:
        """Добавить новый чат"""
        chats = self._read_file("chats.json")
        chats.append(chat_data)
        return self._write_file("chats.json", chats)
    
    def update_chat(self, chat_id: Union[str, int], updated_data: Dict[str, Any]) -> bool:
        """Обновить существующий чат"""
        chats = self._read_file("chats.json")
        chat_id_str = str(chat_id)
        
        for i, chat in enumerate(chats):
            if str(chat.get("chat_id")) == chat_id_str:
                chats[i].update(updated_data)
                return self._write_file("chats.json", chats)
        return False
    
    def delete_chat(self, chat_id: Union[str, int]) -> bool:
        """Удалить чат по ID"""
        chats = self._read_file("chats.json")
        chat_id_str = str(chat_id)
        
        for i, chat in enumerate(chats):
            if str(chat.get("chat_id")) == chat_id_str:
                del chats[i]
                return self._write_file("chats.json", chats)
        return False
    
    def get_chat(self, chat_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        """Получить чат по ID"""
        chats = self._read_file("chats.json")
        chat_id_str = str(chat_id)
        
        for chat in chats:
            if str(chat.get("chat_id")) == chat_id_str:
                return chat
        return None
    
    def get_prefix(self, chat_id: Union[str, int]) -> Optional[str]:
        """Получить префикс чата"""
        chats = self._read_file("chats.json")
        chat_id_str = str(chat_id)
        
        for chat in chats:
            if str(chat.get("chat_id")) == chat_id_str:
                return chat.get("prefix")
        return None
    
    def list_common_chats(self) -> List[Dict[str, Any]]:
        """Список общих чатов"""
        chats = self._read_file("chats.json")
        return [chat for chat in chats if chat.get("is_common", False) and chat.get("active", True)]
    
    # Утилиты для инвентаря
    def list_sizes(self) -> List[str]:
        """Список доступных размеров"""
        inventory = self._read_file("inventory.json")
        return list(inventory.get("sizes", {}).keys())
    
    def list_colors(self, size: str) -> List[str]:
        """Список доступных цветов для размера"""
        inventory = self._read_file("inventory.json")
        size_data = inventory.get("sizes", {}).get(size, {})
        return list(size_data.get("colors", {}).keys())
    
    def reserve(self, size: str, color: str, qty: int = 1) -> bool:
        """Зарезервировать товар"""
        inventory = self._read_file("inventory.json")
        size_data = inventory.get("sizes", {}).get(size, {})
        color_data = size_data.get("colors", {}).get(color, {})
        
        if color_data.get("qty_total", 0) - color_data.get("qty_reserved", 0) >= qty:
            color_data["qty_reserved"] = color_data.get("qty_reserved", 0) + qty
            self._write_file("inventory.json", inventory)
            return True
        return False
    
    def release(self, size: str, color: str, qty: int = 1) -> bool:
        """Освободить зарезервированный товар"""
        inventory = self._read_file("inventory.json")
        size_data = inventory.get("sizes", {}).get(size, {})
        color_data = size_data.get("colors", {}).get(color, {})
        
        if color_data.get("qty_reserved", 0) >= qty:
            color_data["qty_reserved"] = color_data.get("qty_reserved", 0) - qty
            self._write_file("inventory.json", inventory)
            return True
        return False
    
    # Утилиты для заказов
    def create_order(self, payload: Dict[str, Any]) -> int:
        """Создать новый заказ"""
        orders = self._read_file("orders.json")
        
        order_id = self.next_order_id()
        order = {
            "id": order_id,
            "user_tg_id": payload["user_tg_id"],
            "size": payload["size"],
            "color": payload.get("color", "_"),
            "photo_file_id": payload["photo_file_id"],
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "deliveries": []
        }
        
        orders.append(order)
        self._write_file("orders.json", orders)
        
        return order_id
    
    def append_delivery(self, order_id: int, chat_id: Union[str, int], prefix: str, message_id: int) -> bool:
        """Добавить информацию о доставке заказа"""
        orders = self._read_file("orders.json")
        
        for order in orders:
            if order.get("id") == order_id:
                delivery = {
                    "chat_id": str(chat_id),
                    "prefix": prefix,
                    "message_id": message_id
                }
                order["deliveries"].append(delivery)
                order["status"] = "sent"
                self._write_file("orders.json", orders)
                return True
        
        return False
    
    # Устаревшие методы для совместимости
    def get_all(self, filename: str) -> Any:
        """Получить все данные из файла"""
        return self._read_file(filename)
    
    def get(self, filename: str, key: str) -> Optional[Any]:
        """Получить значение по ключу (только для users.json)"""
        if filename == "users.json":
            users = self._read_file(filename)
            return users.get(key)
        return None
    
    def set(self, filename: str, key: str, value: Any) -> bool:
        """Установить значение по ключу (только для users.json)"""
        if filename == "users.json":
            users = self._read_file(filename)
            users[key] = value
            return self._write_file(filename, users)
        return False


# Глобальный экземпляр хранилища
storage = JSONStorage()
