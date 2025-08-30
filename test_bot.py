#!/usr/bin/env python3
"""
Тестовый скрипт для проверки компонентов бота без подключения к Telegram.
"""

import os
import sys
import asyncio
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Тест импортов всех модулей."""
    print("🔍 Тестирование импортов...")
    
    try:
        from config.settings import Settings
        print("✅ config.settings - OK")
        
        from bot.handlers import setup_handlers
        print("✅ bot.handlers - OK")
        
        from bot.keyboards.main import get_main_keyboard
        print("✅ bot.keyboards.main - OK")
        
        from bot.keyboards.catalog import get_catalog_keyboard
        print("✅ bot.keyboards.catalog - OK")
        
        from bot.middlewares import setup_middlewares
        print("✅ bot.middlewares - OK")
        
        from database.models import User, Product, Order
        print("✅ database.models - OK")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def test_settings():
    """Тест настроек."""
    print("\n⚙️ Тестирование настроек...")
    
    try:
        from config.settings import Settings
        
        # Тест с пустыми переменными
        settings = Settings()
        print(f"✅ BOT_TOKEN: {'установлен' if settings.BOT_TOKEN else 'не установлен'}")
        print(f"✅ DATABASE_URL: {settings.DATABASE_URL}")
        print(f"✅ DEBUG: {settings.DEBUG}")
        print(f"✅ LOG_LEVEL: {settings.LOG_LEVEL}")
        
        # Тест парсинга ADMIN_IDS
        admin_ids = settings.get_admin_ids()
        print(f"✅ ADMIN_IDS: {admin_ids}")
        
        # Тест с тестовыми данными
        os.environ['ADMIN_IDS'] = '123,456,789'
        settings2 = Settings()
        admin_ids2 = settings2.get_admin_ids()
        print(f"✅ ADMIN_IDS (тест): {admin_ids2}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка настроек: {e}")
        return False

def test_keyboards():
    """Тест клавиатур."""
    print("\n⌨️ Тестирование клавиатур...")
    
    try:
        from bot.keyboards.main import get_main_keyboard
        from bot.keyboards.catalog import get_catalog_keyboard, get_product_keyboard
        
        main_kb = get_main_keyboard()
        print(f"✅ Главная клавиатура: {len(main_kb.keyboard)} рядов")
        
        catalog_kb = get_catalog_keyboard()
        print(f"✅ Клавиатура каталога: {len(catalog_kb.inline_keyboard)} рядов")
        
        product_kb = get_product_keyboard("test_id")
        print(f"✅ Клавиатура товара: {len(product_kb.inline_keyboard)} рядов")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка клавиатур: {e}")
        return False

def test_database_models():
    """Тест моделей базы данных."""
    print("\n🗄️ Тестирование моделей БД...")
    
    try:
        from database.models import User, Product, Order, Category, OrderItem
        
        # Проверяем, что модели можно создать
        user_fields = [attr for attr in dir(User) if not attr.startswith('_')]
        print(f"✅ User модель: {len(user_fields)} полей")
        
        product_fields = [attr for attr in dir(Product) if not attr.startswith('_')]
        print(f"✅ Product модель: {len(product_fields)} полей")
        
        order_fields = [attr for attr in dir(Order) if not attr.startswith('_')]
        print(f"✅ Order модель: {len(order_fields)} полей")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка моделей БД: {e}")
        return False

async def test_handlers_setup():
    """Тест настройки обработчиков."""
    print("\n🎯 Тестирование обработчиков...")
    
    try:
        from aiogram import Dispatcher
        from bot.handlers import setup_handlers
        from bot.middlewares import setup_middlewares
        
        dp = Dispatcher()
        setup_middlewares(dp)
        setup_handlers(dp)
        
        print(f"✅ Диспетчер настроен успешно")
        print(f"✅ Роутеров подключено: {len(dp.sub_routers)}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка обработчиков: {e}")
        return False

async def main():
    """Главная функция тестирования."""
    print("🚀 Запуск тестирования YaEduMerchBot\n")
    
    tests = [
        ("Импорты", test_imports),
        ("Настройки", test_settings),
        ("Клавиатуры", test_keyboards),
        ("Модели БД", test_database_models),
        ("Обработчики", test_handlers_setup),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✅ {name} - ПРОЙДЕН")
            else:
                print(f"❌ {name} - ПРОВАЛЕН")
        except Exception as e:
            print(f"❌ {name} - ОШИБКА: {e}")
        
        print()
    
    print(f"📊 Результаты тестирования: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены! Бот готов к запуску с реальным токеном.")
        print("\n📋 Для запуска бота:")
        print("1. Получите токен от @BotFather в Telegram")
        print("2. Установите переменные окружения:")
        print("   set BOT_TOKEN=ваш_токен_здесь")
        print("   set ADMIN_IDS=ваш_telegram_id")
        print("3. Запустите: python main.py")
    else:
        print("⚠️ Некоторые тесты провалены. Проверьте ошибки выше.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())
