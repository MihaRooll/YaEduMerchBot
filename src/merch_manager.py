import logging
from typing import Dict, List, Optional, Tuple
from .storage import storage

logger = logging.getLogger(__name__)


class MerchManager:
    """Менеджер для управления мерчем в боте"""
    
    def __init__(self):
        self._init_default_merch()
    
    def _init_default_merch(self):
        """Инициализация базовых значений мерча"""
        # Проверяем, есть ли уже данные
        if not storage.exists("merch_types.json", "types"):
            default_types = ["футболки", "толстовки", "лонгсливы"]
            storage.set("merch_types.json", "types", default_types)
        
        if not storage.exists("merch_colors.json", "colors"):
            default_colors = ["белый", "черный", "серый"]
            storage.set("merch_colors.json", "colors", default_colors)
        
        if not storage.exists("merch_sizes.json", "sizes"):
            default_sizes = ["3XS", "2XS", "XS", "S", "M", "L", "XL", "2XL", "3XL", "4XL", "5XL", "6XL", "7XL", "8XL", "9XL", "10XL"]
            storage.set("merch_sizes.json", "sizes", default_sizes)
    
    # === УПРАВЛЕНИЕ ВИДАМИ МЕРЧА ===
    
    def get_merch_types(self) -> List[str]:
        """Получить список всех видов мерча"""
        return storage.get("merch_types.json", "types") or []
    
    def add_merch_type(self, merch_type: str) -> bool:
        """Добавить новый вид мерча"""
        try:
            types = self.get_merch_types()
            if merch_type.lower() in [t.lower() for t in types]:
                return False  # Уже существует
            
            types.append(merch_type)
            storage.set("merch_types.json", "types", types)
            logger.info(f"Добавлен новый вид мерча: {merch_type}")
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления вида мерча: {e}")
            return False
    
    def remove_merch_type(self, merch_type: str) -> bool:
        """Удалить вид мерча"""
        try:
            types = self.get_merch_types()
            if merch_type not in types:
                return False
            
            types.remove(merch_type)
            storage.set("merch_types.json", "types", types)
            
            # Удаляем все связанные остатки
            self._remove_merch_type_inventory(merch_type)
            
            logger.info(f"Удален вид мерча: {merch_type}")
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления вида мерча: {e}")
            return False
    
    def rename_merch_type(self, old_name: str, new_name: str) -> bool:
        """Переименовать вид мерча"""
        try:
            types = self.get_merch_types()
            if old_name not in types:
                return False
            
            if new_name.lower() in [t.lower() for t in types if t != old_name]:
                return False  # Новое имя уже существует
            
            # Обновляем список типов
            types[types.index(old_name)] = new_name
            storage.set("merch_types.json", "types", types)
            
            # Обновляем инвентарь
            self._rename_merch_type_inventory(old_name, new_name)
            
            logger.info(f"Переименован вид мерча: {old_name} -> {new_name}")
            return True
        except Exception as e:
            logger.error(f"Ошибка переименования вида мерча: {e}")
            return False
    
    # === УПРАВЛЕНИЕ ЦВЕТАМИ ===
    
    def get_colors(self) -> List[str]:
        """Получить список всех цветов"""
        return storage.get("merch_colors.json", "colors") or []
    
    def add_color(self, color: str) -> bool:
        """Добавить новый цвет"""
        try:
            colors = self.get_colors()
            if color.lower() in [c.lower() for c in colors]:
                return False
            
            colors.append(color)
            storage.set("merch_colors.json", "colors", colors)
            logger.info(f"Добавлен новый цвет: {color}")
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления цвета: {e}")
            return False
    
    def remove_color(self, color: str) -> bool:
        """Удалить цвет"""
        try:
            colors = self.get_colors()
            if color not in colors:
                return False
            
            colors.remove(color)
            storage.set("merch_colors.json", "colors", colors)
            
            # Удаляем все связанные остатки
            self._remove_color_inventory(color)
            
            logger.info(f"Удален цвет: {color}")
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления цвета: {e}")
            return False
    
    def rename_color(self, old_name: str, new_name: str) -> bool:
        """Переименовать цвет"""
        try:
            colors = self.get_colors()
            if old_name not in colors:
                return False
            
            if new_name.lower() in [c.lower() for c in colors if c != old_name]:
                return False
            
            colors[colors.index(old_name)] = new_name
            storage.set("merch_colors.json", "colors", colors)
            
            # Обновляем инвентарь
            self._rename_color_inventory(old_name, new_name)
            
            logger.info(f"Переименован цвет: {old_name} -> {new_name}")
            return True
        except Exception as e:
            logger.error(f"Ошибка переименования цвета: {e}")
            return False
    
    # === УПРАВЛЕНИЕ РАЗМЕРАМИ ===
    
    def get_sizes(self) -> List[str]:
        """Получить список всех размеров"""
        return storage.get("merch_sizes.json", "sizes") or []
    
    def add_size(self, size: str) -> bool:
        """Добавить новый размер"""
        try:
            sizes = self.get_sizes()
            if size in sizes:
                return False
            
            sizes.append(size)
            storage.set("merch_sizes.json", "sizes", sizes)
            logger.info(f"Добавлен новый размер: {size}")
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления размера: {e}")
            return False
    
    def remove_size(self, size: str) -> bool:
        """Удалить размер"""
        try:
            sizes = self.get_sizes()
            if size not in sizes:
                return False
            
            sizes.remove(size)
            storage.set("merch_sizes.json", "sizes", sizes)
            
            # Удаляем все связанные остатки
            self._remove_size_inventory(size)
            
            logger.info(f"Удален размер: {size}")
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления размера: {e}")
            return False
    
    def rename_size(self, old_name: str, new_name: str) -> bool:
        """Переименовать размер"""
        try:
            sizes = self.get_sizes()
            if old_name not in sizes:
                return False
            
            if new_name in sizes:
                return False
            
            sizes[sizes.index(old_name)] = new_name
            storage.set("merch_sizes.json", "sizes", sizes)
            
            # Обновляем инвентарь
            self._rename_size_inventory(old_name, new_name)
            
            logger.info(f"Переименован размер: {old_name} -> {new_name}")
            return True
        except Exception as e:
            logger.error(f"Ошибка переименования размера: {e}")
            return False
    
    # === УПРАВЛЕНИЕ ОСТАТКАМИ ===
    
    def get_inventory_key(self, merch_type: str, color: str, size: str) -> str:
        """Создать ключ для инвентаря"""
        return f"{merch_type}_{color}_{size}"
    
    def set_stock(self, merch_type: str, color: str, size: str, quantity: int) -> bool:
        """Установить остаток по конкретному виду/цвету/размеру"""
        try:
            key = self.get_inventory_key(merch_type, color, size)
            inventory = storage.get_all("inventory.json")
            
            inventory[key] = {
                "merch_type": merch_type,
                "color": color,
                "size": size,
                "qty_total": max(0, quantity),
                "qty_reserved": 0,
                "qty_available": max(0, quantity)
            }
            
            storage._write_file("inventory.json", inventory)
            logger.info(f"Установлен остаток {merch_type} {color} {size}: {quantity}")
            return True
        except Exception as e:
            logger.error(f"Ошибка установки остатка: {e}")
            return False
    
    def increase_stock(self, merch_type: str, color: str, size: str, quantity: int) -> bool:
        """Увеличить остаток (при поступлении)"""
        try:
            key = self.get_inventory_key(merch_type, color, size)
            inventory = storage.get_all("inventory.json")
            
            if key in inventory:
                inventory[key]["qty_total"] += quantity
                inventory[key]["qty_available"] = inventory[key]["qty_total"] - inventory[key]["qty_reserved"]
            else:
                inventory[key] = {
                    "merch_type": merch_type,
                    "color": color,
                    "size": size,
                    "qty_total": quantity,
                    "qty_reserved": 0,
                    "qty_available": quantity
                }
            
            storage._write_file("inventory.json", inventory)
            logger.info(f"Увеличен остаток {merch_type} {color} {size} на {quantity}")
            return True
        except Exception as e:
            logger.error(f"Ошибка увеличения остатка: {e}")
            return False
    
    def decrease_stock(self, merch_type: str, color: str, size: str, quantity: int) -> bool:
        """Уменьшить остаток (при продаже/списании)"""
        try:
            key = self.get_inventory_key(merch_type, color, size)
            inventory = storage.get_all("inventory.json")
            
            if key not in inventory:
                return False
            
            current_stock = inventory[key]["qty_available"]
            if current_stock < quantity:
                return False
            
            inventory[key]["qty_total"] -= quantity
            inventory[key]["qty_available"] = inventory[key]["qty_total"] - inventory[key]["qty_reserved"]
            
            storage._write_file("inventory.json", inventory)
            logger.info(f"Уменьшен остаток {merch_type} {color} {size} на {quantity}")
            return True
        except Exception as e:
            logger.error(f"Ошибка уменьшения остатка: {e}")
            return False
    
    def reserve_stock(self, merch_type: str, color: str, size: str, quantity: int) -> bool:
        """Зарезервировать товар (при оформлении заказа)"""
        try:
            key = self.get_inventory_key(merch_type, color, size)
            inventory = storage.get_all("inventory.json")
            
            if key not in inventory:
                return False
            
            if inventory[key]["qty_available"] < quantity:
                return False
            
            inventory[key]["qty_reserved"] += quantity
            inventory[key]["qty_available"] = inventory[key]["qty_total"] - inventory[key]["qty_reserved"]
            
            storage._write_file("inventory.json", inventory)
            logger.info(f"Зарезервировано {merch_type} {color} {size}: {quantity}")
            return True
        except Exception as e:
            logger.error(f"Ошибка резервирования: {e}")
            return False
    
    def release_reserved_stock(self, merch_type: str, color: str, size: str, quantity: int) -> bool:
        """Освободить зарезервированный товар"""
        try:
            key = self.get_inventory_key(merch_type, color, size)
            inventory = storage.get_all("inventory.json")
            
            if key not in inventory:
                return False
            
            if inventory[key]["qty_reserved"] < quantity:
                return False
            
            inventory[key]["qty_reserved"] -= quantity
            inventory[key]["qty_available"] = inventory[key]["qty_total"] - inventory[key]["qty_reserved"]
            
            storage._write_file("inventory.json", inventory)
            logger.info(f"Освобождено резервирование {merch_type} {color} {size}: {quantity}")
            return True
        except Exception as e:
            logger.error(f"Ошибка освобождения резервирования: {e}")
            return False
    
    def get_stock(self, merch_type: str, color: str, size: str) -> Optional[Dict]:
        """Получить информацию об остатках"""
        try:
            key = self.get_inventory_key(merch_type, color, size)
            inventory = storage.get_all("inventory.json")
            return inventory.get(key)
        except Exception as e:
            logger.error(f"Ошибка получения остатка: {e}")
            return None
    
    def get_all_stocks(self) -> Dict[str, Dict]:
        """Получить все остатки"""
        try:
            return storage.get_all("inventory.json")
        except Exception as e:
            logger.error(f"Ошибка получения всех остатков: {e}")
            return {}
    
    def get_stock_report(self) -> str:
        """Получить отчет по остаткам"""
        try:
            inventory = self.get_all_stocks()
            if not inventory:
                return "📦 <b>Отчет по остаткам</b>\n\n❌ Нет данных об остатках"
            
            report = "📦 <b>Отчет по остаткам</b>\n\n"
            
            # Группируем по типу мерча
            merch_groups = {}
            for key, item in inventory.items():
                merch_type = item.get("merch_type", "Неизвестно")
                if merch_type not in merch_groups:
                    merch_groups[merch_type] = []
                merch_groups[merch_type].append(item)
            
            for merch_type, items in merch_groups.items():
                report += f"<b>{merch_type.upper()}</b>\n"
                
                # Группируем по цвету
                color_groups = {}
                for item in items:
                    color = item.get("color", "Неизвестно")
                    if color not in color_groups:
                        color_groups[color] = []
                    color_groups[color].append(item)
                
                for color, color_items in color_groups.items():
                    report += f"  🎨 <b>{color}</b>:\n"
                    
                    # Сортируем по размеру
                    color_items.sort(key=lambda x: self._get_size_order(x.get("size", "")))
                    
                    for item in color_items:
                        size = item.get("size", "Неизвестно")
                        total = item.get("qty_total", 0)
                        reserved = item.get("qty_reserved", 0)
                        available = item.get("qty_available", 0)
                        
                        status_emoji = "🟢" if available > 5 else "🟡" if available > 0 else "🔴"
                        report += f"    {status_emoji} {size}: {available}/{total} (резерв: {reserved})\n"
                    
                    report += "\n"
                
                report += "\n"
            
            return report
        except Exception as e:
            logger.error(f"Ошибка формирования отчета: {e}")
            return "❌ Ошибка формирования отчета"
    
    def _get_size_order(self, size: str) -> int:
        """Получить порядковый номер размера для сортировки"""
        size_order = {
            "3XS": 1, "2XS": 2, "XS": 3, "S": 4, "M": 5, "L": 6,
            "XL": 7, "2XL": 8, "3XL": 9, "4XL": 10, "5XL": 11,
            "6XL": 12, "7XL": 13, "8XL": 14, "9XL": 15, "10XL": 16
        }
        return size_order.get(size, 999)
    
    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
    
    def _remove_merch_type_inventory(self, merch_type: str):
        """Удалить все остатки по типу мерча"""
        try:
            inventory = storage.get_all("inventory.json")
            keys_to_remove = [key for key, item in inventory.items() 
                             if item.get("merch_type") == merch_type]
            
            for key in keys_to_remove:
                del inventory[key]
            
            storage._write_file("inventory.json", inventory)
        except Exception as e:
            logger.error(f"Ошибка удаления остатков типа мерча: {e}")
    
    def _remove_color_inventory(self, color: str):
        """Удалить все остатки по цвету"""
        try:
            inventory = storage.get_all("inventory.json")
            keys_to_remove = [key for key, item in inventory.items() 
                             if item.get("color") == color]
            
            for key in keys_to_remove:
                del inventory[key]
            
            storage._write_file("inventory.json", inventory)
        except Exception as e:
            logger.error(f"Ошибка удаления остатков цвета: {e}")
    
    def _remove_size_inventory(self, size: str):
        """Удалить все остатки по размеру"""
        try:
            inventory = storage.get_all("inventory.json")
            keys_to_remove = [key for key, item in inventory.items() 
                             if item.get("size") == size]
            
            for key in keys_to_remove:
                del inventory[key]
            
            storage._write_file("inventory.json", inventory)
        except Exception as e:
            logger.error(f"Ошибка удаления остатков размера: {e}")
    
    def _rename_merch_type_inventory(self, old_name: str, new_name: str):
        """Переименовать тип мерча в инвентаре"""
        try:
            inventory = storage.get_all("inventory.json")
            for key, item in inventory.items():
                if item.get("merch_type") == old_name:
                    item["merch_type"] = new_name
                    # Обновляем ключ
                    new_key = self.get_inventory_key(new_name, item.get("color"), item.get("size"))
                    if new_key != key:
                        inventory[new_key] = item
                        del inventory[key]
            
            storage._write_file("inventory.json", inventory)
        except Exception as e:
            logger.error(f"Ошибка переименования типа мерча в инвентаре: {e}")
    
    def _rename_color_inventory(self, old_name: str, new_name: str):
        """Переименовать цвет в инвентаре"""
        try:
            inventory = storage.get_all("inventory.json")
            for key, item in inventory.items():
                if item.get("color") == old_name:
                    item["color"] = new_name
                    # Обновляем ключ
                    new_key = self.get_inventory_key(item.get("merch_type"), new_name, item.get("size"))
                    if new_key != key:
                        inventory[new_key] = item
                        del inventory[key]
            
            storage._write_file("inventory.json", inventory)
        except Exception as e:
            logger.error(f"Ошибка переименования цвета в инвентаре: {e}")
    
    def _rename_size_inventory(self, old_name: str, new_name: str):
        """Переименовать размер в инвентаре"""
        try:
            inventory = storage.get_all("inventory.json")
            for key, item in inventory.items():
                if item.get("size") == old_name:
                    item["size"] = new_name
                    # Обновляем ключ
                    new_key = self.get_inventory_key(item.get("merch_type"), item.get("color"), new_name)
                    if new_key != key:
                        inventory[new_key] = item
                        del inventory[key]
            
            storage._write_file("inventory.json", inventory)
        except Exception as e:
            logger.error(f"Ошибка переименования размера в инвентаре: {e}")
    
    def check_availability(self, merch_type: str, color: str, size: str, quantity: int = 1) -> bool:
        """Проверить доступность товара"""
        stock = self.get_stock(merch_type, color, size)
        if not stock:
            return False
        
        return stock.get("qty_available", 0) >= quantity
    
    def get_low_stock_items(self, threshold: int = 5) -> List[Dict]:
        """Получить товары с низким остатком"""
        try:
            inventory = self.get_all_stocks()
            low_stock = []
            
            for item in inventory.values():
                if item.get("qty_available", 0) <= threshold:
                    low_stock.append(item)
            
            return low_stock
        except Exception as e:
            logger.error(f"Ошибка получения товаров с низким остатком: {e}")
            return []


# Создаем глобальный экземпляр менеджера
merch_manager = MerchManager()
