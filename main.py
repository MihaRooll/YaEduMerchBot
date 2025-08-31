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
        # Создаем и запускаем бота
        bot = YaEduMerchBot(settings.BOT_TOKEN)
        bot.run()
        
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        raise


if __name__ == "__main__":
    main()
