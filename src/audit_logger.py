import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from .storage import storage

# Настройка отдельного логгера для аудита
audit_logger = logging.getLogger('audit')
audit_handler = logging.FileHandler('audit.log', encoding='utf-8')
audit_formatter = logging.Formatter('%(asctime)s - %(message)s')
audit_handler.setFormatter(audit_formatter)
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)
audit_logger.propagate = False  # Не передавать в основной логгер


class AuditLogger:
    """Система аудита для логирования всех действий администраторов"""
    
    @staticmethod
    def log_action(actor_id: int, action: str, target: str, details: Dict[str, Any] = None, 
                   target_id: Optional[str] = None):
        """
        Логирует действие пользователя
        
        Args:
            actor_id: ID пользователя, который выполняет действие
            action: Тип действия (add_user, change_role, block_user, etc.)
            target: Тип объекта (user, chat, order, etc.)
            details: Дополнительные детали действия
            target_id: ID объекта, над которым выполняется действие
        """
        try:
            # Получаем данные актора
            actor_data = storage.get("users.json", str(actor_id))
            actor_name = actor_data.get('first_name', 'Unknown') if actor_data else 'System'
            actor_role = actor_data.get('role', 'unknown') if actor_data else 'system'
            
            # Формируем запись аудита
            audit_record = {
                'timestamp': datetime.now().isoformat(),
                'actor_id': actor_id,
                'actor_name': actor_name,
                'actor_role': actor_role,
                'action': action,
                'target': target,
                'target_id': target_id,
                'details': details or {},
                'success': True
            }
            
            # Логируем в файл
            audit_logger.info(json.dumps(audit_record, ensure_ascii=False))
            
            # Сохраняем в JSON для быстрого доступа
            AuditLogger._save_to_storage(audit_record)
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Ошибка записи аудита: {e}")
    
    @staticmethod
    def log_failed_action(actor_id: int, action: str, target: str, error: str, 
                         target_id: Optional[str] = None):
        """Логирует неудачное действие"""
        try:
            actor_data = storage.get("users.json", str(actor_id))
            actor_name = actor_data.get('first_name', 'Unknown') if actor_data else 'System'
            actor_role = actor_data.get('role', 'unknown') if actor_data else 'system'
            
            audit_record = {
                'timestamp': datetime.now().isoformat(),
                'actor_id': actor_id,
                'actor_name': actor_name,
                'actor_role': actor_role,
                'action': action,
                'target': target,
                'target_id': target_id,
                'error': error,
                'success': False
            }
            
            audit_logger.warning(json.dumps(audit_record, ensure_ascii=False))
            AuditLogger._save_to_storage(audit_record)
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Ошибка записи аудита неудачи: {e}")
    
    @staticmethod
    def _save_to_storage(record: Dict[str, Any]):
        """Сохраняет запись аудита в JSON хранилище"""
        try:
            # Генерируем уникальный ID для записи
            record_id = f"{record['timestamp']}_{record['actor_id']}_{record['action']}"
            storage.set("audit_log.json", record_id, record)
        except Exception as e:
            logging.getLogger(__name__).error(f"Ошибка сохранения аудита в storage: {e}")
    
    @staticmethod
    def get_recent_actions(limit: int = 50) -> list:
        """Получает последние действия из аудита"""
        try:
            all_records = storage.get_all("audit_log.json")
            # Сортируем по времени (новые первыми)
            sorted_records = sorted(
                all_records.values(), 
                key=lambda x: x.get('timestamp', ''), 
                reverse=True
            )
            return sorted_records[:limit]
        except Exception as e:
            logging.getLogger(__name__).error(f"Ошибка получения записей аудита: {e}")
            return []
    
    @staticmethod
    def get_user_actions(user_id: int, limit: int = 20) -> list:
        """Получает действия конкретного пользователя"""
        try:
            all_records = storage.get_all("audit_log.json")
            user_records = [
                record for record in all_records.values()
                if record.get('actor_id') == user_id
            ]
            # Сортируем по времени (новые первыми)
            sorted_records = sorted(
                user_records, 
                key=lambda x: x.get('timestamp', ''), 
                reverse=True
            )
            return sorted_records[:limit]
        except Exception as e:
            logging.getLogger(__name__).error(f"Ошибка получения действий пользователя: {e}")
            return []
    
    @staticmethod
    def get_actions_by_target(target: str, target_id: str, limit: int = 20) -> list:
        """Получает действия над конкретным объектом"""
        try:
            all_records = storage.get_all("audit_log.json")
            target_records = [
                record for record in all_records.values()
                if record.get('target') == target and record.get('target_id') == target_id
            ]
            # Сортируем по времени (новые первыми)
            sorted_records = sorted(
                target_records, 
                key=lambda x: x.get('timestamp', ''), 
                reverse=True
            )
            return sorted_records[:limit]
        except Exception as e:
            logging.getLogger(__name__).error(f"Ошибка получения действий над объектом: {e}")
            return []


# Удобные функции для логирования конкретных действий
def log_user_added(actor_id: int, target_user_id: int, role: str, username: str):
    """Логирует добавление пользователя"""
    AuditLogger.log_action(
        actor_id=actor_id,
        action="add_user",
        target="user",
        target_id=str(target_user_id),
        details={
            "new_role": role,
            "username": username
        }
    )

def log_role_changed(actor_id: int, target_user_id: int, old_role: str, new_role: str):
    """Логирует изменение роли"""
    AuditLogger.log_action(
        actor_id=actor_id,
        action="change_role",
        target="user",
        target_id=str(target_user_id),
        details={
            "old_role": old_role,
            "new_role": new_role
        }
    )

def log_user_blocked(actor_id: int, target_user_id: int, reason: str = ""):
    """Логирует блокировку пользователя"""
    AuditLogger.log_action(
        actor_id=actor_id,
        action="block_user",
        target="user",
        target_id=str(target_user_id),
        details={
            "reason": reason
        }
    )

def log_user_unblocked(actor_id: int, target_user_id: int):
    """Логирует разблокировку пользователя"""
    AuditLogger.log_action(
        actor_id=actor_id,
        action="unblock_user",
        target="user",
        target_id=str(target_user_id)
    )

def log_chat_coordinator_assigned(actor_id: int, chat_id: str, coordinator_id: int):
    """Логирует назначение координатора на чат"""
    AuditLogger.log_action(
        actor_id=actor_id,
        action="assign_coordinator",
        target="chat",
        target_id=chat_id,
        details={
            "coordinator_id": coordinator_id
        }
    )

def log_order_action(actor_id: int, order_id: str, action: str, details: Dict[str, Any] = None):
    """Логирует действия с заказами"""
    AuditLogger.log_action(
        actor_id=actor_id,
        action=f"order_{action}",
        target="order",
        target_id=order_id,
        details=details or {}
    )
