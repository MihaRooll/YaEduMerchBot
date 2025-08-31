import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from .storage import storage
from .audit_logger import log_user_added, log_role_changed, log_user_blocked, log_user_unblocked
from config import settings

logger = logging.getLogger(__name__)


class RoleManager:
    """Менеджер ролей и авторизации"""
    
    # Иерархия ролей (от высшей к низшей)
    ROLES = {
        "admin": 4,      # Админ - может все
        "coordinator": 3, # Координатор - может добавлять промо
        "promo": 2,       # Промо - может работать с заказами
        "user": 1         # Пользователь - базовые права
    }
    
    def __init__(self):
        self._init_main_admin()
    
    def _init_main_admin(self):
        """Инициализация главного админа"""
        main_admin_id = str(settings.MAIN_ADMIN_ID)
        if not storage.get("users.json", main_admin_id):
            admin_data = {
                "username": "main_admin",
                "first_name": "Главный Администратор",
                "last_name": "",
                "role": "admin",
                "added_by": "system",
                "added_at": datetime.now().isoformat(),
                "is_active": True,
                "total_orders": 0
            }
            storage.set("users.json", main_admin_id, admin_data)
            logger.info(f"Создан главный админ: {main_admin_id}")
    
    def get_user_role(self, user_id: int) -> str:
        """Получить роль пользователя"""
        user_data = storage.get("users.json", str(user_id))
        if user_data and user_data.get("is_active", False):
            return user_data.get("role", "user")
        return "user"
    
    def get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить данные пользователя"""
        return storage.get("users.json", str(user_id))
    
    def has_permission(self, user_id: int, required_role: str) -> bool:
        """Проверить права пользователя"""
        user_role = self.get_user_role(user_id)
        user_level = self.ROLES.get(user_role, 0)
        required_level = self.ROLES.get(required_role, 0)
        return user_level >= required_level
    
    def can_add_role(self, user_id: int, target_role: str) -> bool:
        """Проверить может ли пользователь добавить роль"""
        user_role = self.get_user_role(user_id)
        
        if user_role == "admin":
            return True  # Админ может все
        elif user_role == "coordinator" and target_role == "promo":
            return True  # Координатор может добавлять промо
        else:
            return False
    
    def add_user(self, user_id: int, username: str, first_name: str, 
                 role: str, added_by: int) -> bool:
        """Добавить пользователя с ролью"""
        # Проверяем права того кто добавляет
        if not self.can_add_role(added_by, role):
            logger.warning(f"Пользователь {added_by} не может добавить роль {role}")
            return False
        
        # Проверяем что роль валидна
        if role not in self.ROLES:
            logger.error(f"Неизвестная роль: {role}")
            return False
        
        user_data = {
            "username": username,
            "first_name": first_name,
            "last_name": "",
            "role": role,
            "added_by": str(added_by),
            "added_at": datetime.now().isoformat(),
            "is_active": True,
            "blocked": False,
            "assigned_chats": [],  # Для координаторов - список чатов
            "total_orders": 0
        }
        
        storage.set("users.json", str(user_id), user_data)
        log_user_added(added_by, user_id, role, username)
        logger.info(f"Добавлен пользователь {user_id} с ролью {role}")
        return True
    
    def update_user_role(self, user_id: int, new_role: str, updated_by: int) -> bool:
        """Обновить роль пользователя"""
        # Проверяем права
        if not self.can_add_role(updated_by, new_role):
            return False
        
        user_data = storage.get("users.json", str(user_id))
        if not user_data:
            return False
        
        old_role = user_data.get("role", "user")
        user_data["role"] = new_role
        user_data["updated_by"] = str(updated_by)
        user_data["updated_at"] = datetime.now().isoformat()
        
        storage.set("users.json", str(user_id), user_data)
        log_role_changed(updated_by, user_id, old_role, new_role)
        logger.info(f"Обновлена роль пользователя {user_id} на {new_role}")
        return True
    
    def deactivate_user(self, user_id: int, deactivated_by: int) -> bool:
        """Деактивировать пользователя"""
        # Проверяем права
        if not self.has_permission(deactivated_by, "coordinator"):
            return False
        
        user_data = storage.get("users.json", str(user_id))
        if not user_data:
            return False
        
        user_data["is_active"] = False
        user_data["deactivated_by"] = str(deactivated_by)
        user_data["deactivated_at"] = datetime.now().isoformat()
        
        storage.set("users.json", str(user_id), user_data)
        logger.info(f"Деактивирован пользователь {user_id}")
        return True
    
    def get_users_by_role(self, role: str) -> List[Dict[str, Any]]:
        """Получить всех пользователей с определенной ролью"""
        users = storage.get_all("users.json")
        return [
            {"user_id": user_id, **user_data}
            for user_id, user_data in users.items()
            if user_data.get("role") == role and user_data.get("is_active", False)
        ]
    
    def get_all_active_users(self) -> List[Dict[str, Any]]:
        """Получить всех активных пользователей"""
        users = storage.get_all("users.json")
        return [
            {"user_id": user_id, **user_data}
            for user_id, user_data in users.items()
            if user_data.get("is_active", False)
        ]
    
    def block_user(self, user_id: int, blocked_by: int, reason: str = "") -> bool:
        """Заблокировать пользователя"""
        # Проверяем права (только админы могут блокировать)
        if not self.has_permission(blocked_by, "admin"):
            return False
        
        user_data = storage.get("users.json", str(user_id))
        if not user_data:
            return False
        
        user_data["blocked"] = True
        user_data["blocked_by"] = str(blocked_by)
        user_data["blocked_at"] = datetime.now().isoformat()
        user_data["block_reason"] = reason
        
        storage.set("users.json", str(user_id), user_data)
        log_user_blocked(blocked_by, user_id, reason)
        logger.info(f"Заблокирован пользователь {user_id}")
        return True
    
    def unblock_user(self, user_id: int, unblocked_by: int) -> bool:
        """Разблокировать пользователя"""
        # Проверяем права (только админы могут разблокировать)
        if not self.has_permission(unblocked_by, "admin"):
            return False
        
        user_data = storage.get("users.json", str(user_id))
        if not user_data:
            return False
        
        user_data["blocked"] = False
        user_data["unblocked_by"] = str(unblocked_by)
        user_data["unblocked_at"] = datetime.now().isoformat()
        
        storage.set("users.json", str(user_id), user_data)
        log_user_unblocked(unblocked_by, user_id)
        logger.info(f"Разблокирован пользователь {user_id}")
        return True
    
    def is_user_blocked(self, user_id: int) -> bool:
        """Проверить заблокирован ли пользователь"""
        user_data = storage.get("users.json", str(user_id))
        return user_data.get("blocked", False) if user_data else False
    
    def assign_coordinator_to_chat(self, coordinator_id: int, chat_id: str, assigned_by: int) -> bool:
        """Назначить координатора на чат"""
        # Проверяем права (только админы могут назначать координаторов)
        if not self.has_permission(assigned_by, "admin"):
            return False
        
        # Проверяем что пользователь является координатором
        coordinator_data = storage.get("users.json", str(coordinator_id))
        if not coordinator_data or coordinator_data.get("role") != "coordinator":
            return False
        
        # Добавляем чат в список назначенных чатов координатора
        assigned_chats = coordinator_data.get("assigned_chats", [])
        if chat_id not in assigned_chats:
            assigned_chats.append(chat_id)
            coordinator_data["assigned_chats"] = assigned_chats
            storage.set("users.json", str(coordinator_id), coordinator_data)
        
        # Обновляем данные чата
        chat_data = storage.get_chat(chat_id)
        if chat_data:
            chat_data["coordinator_id"] = str(coordinator_id)
            chat_data["assigned_by"] = str(assigned_by)
            chat_data["assigned_at"] = datetime.now().isoformat()
            storage.update_chat(chat_id, chat_data)
        
        from .audit_logger import log_chat_coordinator_assigned
        log_chat_coordinator_assigned(assigned_by, chat_id, coordinator_id)
        logger.info(f"Координатор {coordinator_id} назначен на чат {chat_id}")
        return True
    
    def get_coordinator_chats(self, coordinator_id: int) -> List[str]:
        """Получить список чатов координатора"""
        coordinator_data = storage.get("users.json", str(coordinator_id))
        if not coordinator_data or coordinator_data.get("role") != "coordinator":
            return []
        return coordinator_data.get("assigned_chats", [])
    
    def search_users(self, query: str, searcher_id: int) -> List[Dict[str, Any]]:
        """Поиск пользователей по ID или username"""
        # Проверяем права (минимум координатор)
        if not self.has_permission(searcher_id, "coordinator"):
            return []
        
        users = storage.get_all("users.json")
        results = []
        
        query_lower = query.lower()
        
        for user_id, user_data in users.items():
            # Поиск по ID
            if query in user_id:
                results.append({"user_id": user_id, **user_data})
                continue
            
            # Поиск по username
            username = user_data.get("username", "").lower()
            if query_lower in username:
                results.append({"user_id": user_id, **user_data})
                continue
            
            # Поиск по имени
            first_name = user_data.get("first_name", "").lower()
            if query_lower in first_name:
                results.append({"user_id": user_id, **user_data})
        
        return results[:20]  # Ограничиваем результаты
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Получить статистику пользователей"""
        users = storage.get_all("users.json")
        
        stats = {
            "total_users": len(users),
            "active_users": 0,
            "blocked_users": 0,
            "by_role": {role: 0 for role in self.ROLES.keys()}
        }
        
        for user_data in users.values():
            if user_data.get("is_active", False):
                stats["active_users"] += 1
            
            if user_data.get("blocked", False):
                stats["blocked_users"] += 1
            
            role = user_data.get("role", "user")
            if role in stats["by_role"]:
                stats["by_role"][role] += 1
        
        return stats


# Глобальный экземпляр менеджера ролей
role_manager = RoleManager()
