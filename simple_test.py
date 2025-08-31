print("Начинаем тест...")

try:
    print("1. Импорт config...")
    from config import settings
    print("   ✅ config загружен")
except Exception as e:
    print(f"   ❌ Ошибка config: {e}")
    import traceback
    traceback.print_exc()

try:
    print("2. Импорт src.bot...")
    from src.bot import YaEduMerchBot
    print("   ✅ bot загружен")
except Exception as e:
    print(f"   ❌ Ошибка bot: {e}")
    import traceback
    traceback.print_exc()

print("Тест завершен")
