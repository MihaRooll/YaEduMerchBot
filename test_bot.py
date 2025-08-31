#!/usr/bin/env python3
"""Тестовый скрипт для проверки импорта бота"""

import sys
import traceback

def test_imports():
    """Тестирует импорт всех модулей"""
    print("=== Тест импорта модулей ===")
    
    try:
        print("1. Импорт config...")
        from config import settings
        print("   ✅ config загружен успешно")
        print(f"   BOT_TOKEN: {settings.BOT_TOKEN}")
        print(f"   MAIN_ADMIN_ID: {settings.MAIN_ADMIN_ID}")
    except Exception as e:
        print(f"   ❌ Ошибка импорта config: {e}")
        traceback.print_exc()
        return False
    
    try:
        print("2. Импорт src.bot...")
        from src.bot import YaEduMerchBot
        print("   ✅ src.bot загружен успешно")
    except Exception as e:
        print(f"   ❌ Ошибка импорта src.bot: {e}")
        traceback.print_exc()
        return False
    
    try:
        print("3. Импорт src.handlers.merch_settings...")
        from src.handlers.merch_settings import MerchSettingsStates
        print("   ✅ merch_settings загружен успешно")
        print(f"   Состояния FSM: {list(MerchSettingsStates.states)}")
    except Exception as e:
        print(f"   ❌ Ошибка импорта merch_settings: {e}")
        traceback.print_exc()
        return False
    
    print("\n=== Все модули загружены успешно! ===")
    return True

if __name__ == "__main__":
    success = test_imports()
    if success:
        print("\n🎉 Бот готов к запуску!")
    else:
        print("\n💥 Есть проблемы с импортом!")
        sys.exit(1)
