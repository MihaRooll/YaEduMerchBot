import logging
from src.bot import YaEduMerchBot
from config import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Основная функция запуска бота"""
    try:
        # Проверяем токен бота
        if not settings.BOT_TOKEN:
            logger.error("❌ BOT_TOKEN не установлен!")
            print("\n" + "="*50)
            print("❌ ОШИБКА: BOT_TOKEN не установлен!")
            print("="*50)
            print("\nДля запуска бота необходимо:")
            print("1. Создать бота через @BotFather")
            print("2. Получить токен")
            print("3. Установить переменную окружения BOT_TOKEN")
            print("\nПримеры:")
            print("Windows (PowerShell):")
            print("  $env:BOT_TOKEN='ваш_токен_здесь'")
            print("  python main.py")
            print("\nWindows (CMD):")
            print("  set BOT_TOKEN=ваш_токен_здесь")
            print("  python main.py")
            print("\nLinux/Mac:")
            print("  export BOT_TOKEN=ваш_токен_здесь")
            print("  python main.py")
            print("\nИли создать файл .env в корне проекта:")
            print("  BOT_TOKEN=ваш_токен_здесь")
            print("  MAIN_ADMIN_ID=445075408")
            print("\n" + "="*50)
            return
        
        # Создаем и запускаем бота
        logger.info(f"Запуск бота с токеном: {settings.BOT_TOKEN[:10]}...")
        bot = YaEduMerchBot(settings.BOT_TOKEN)
        bot.run()
        
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        raise


if __name__ == "__main__":
    main()
