import os
import json
import logging
import sys
import asyncio
import signal
from dotenv import load_dotenv
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, 
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ConversationHandler, 
    CallbackQueryHandler, 
    ContextTypes
)
from telegram.error import TimedOut, NetworkError, RetryAfter, Conflict, InvalidToken

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
WEBAPP_URL = "https://xomakone3.github.io/clothing-storese/redirect.html"
WEBAPP_IMAGES_DIR = "webapp/images"
PRODUCTS_FILE = "webapp/products.json"

# Состояния для ConversationHandler
TITLE, DESCRIPTION, PRICE, SIZES, COLORS, PHOTO = range(6)

def load_products():
    """Загружаем товары из JSON файла"""
    try:
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        logger.error("Ошибка декодирования JSON")
        return []

def save_products(products):
    """Сохраняем товары в JSON файл"""
    with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

def retry_with_backoff(max_retries=3, base_delay=1):
    """Декоратор для повторных попыток с экспоненциальной задержкой"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return await func(*args, **kwargs)
                except (TimedOut, NetworkError, RetryAfter, Conflict) as e:
                    retries += 1
                    delay = base_delay * (2 ** retries)
                    logger.warning(f"Ошибка сети: {e}. Попытка {retries}/{max_retries}. Ожидание {delay} сек.")
                    
                    if isinstance(e, RetryAfter):
                        delay = max(delay, e.retry_after)
                    
                    await asyncio.sleep(delay)
                except Exception as e:
                    logger.error(f"Непредвиденная ошибка: {e}")
                    raise
            
            logger.error("Превышено максимальное количество попыток")
            raise
        return wrapper
    return decorator

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🛍️ Каталог", web_app=WebAppInfo(url=WEBAPP_URL)),
            InlineKeyboardButton("📦 Корзина", callback_data='cart')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "👋 Добро пожаловать в наш магазин!\n\n"
        "Выберите, что вас интересует:"
    )
    
    await update.message.reply_text(
        welcome_text, 
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    if update.effective_user.id == int(ADMIN_ID):
        help_text = """
Доступные команды:
/start - Начать работу с ботом
/help - Показать список команд
/list_products - Показать список товаров
/add_product - Добавить новый товар
/delete_product - Удалить товар
"""
    else:
        help_text = """
Доступные команды:
/start - Начать работу с ботом
/help - Показать список команд
/list_products - Показать список товаров
"""
    await update.message.reply_text(help_text)

async def list_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список всех товаров"""
    if update.effective_user.id != int(ADMIN_ID):
        await update.message.reply_text("У вас нет прав администратора.")
        return

    products_data = load_products()
    
    if not products_data:
        await update.message.reply_text("Товаров пока нет.")
        return
    
    response = "Список товаров:\n\n"
    for product in products_data:
        response += f"ID: {product['id']}\n"
        response += f"Название: {product['name']}\n"
        response += f"Описание: {product['description']}\n"
        response += f"Цена: {product['price']}₽\n"
        response += "-------------------\n"

    await update.message.reply_text(response)

async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало добавления нового товара"""
    if update.effective_user.id != int(ADMIN_ID):
        await update.message.reply_text("У вас нет прав администратора.")
        return

    await update.message.reply_text("Введите название товара:")
    return TITLE

async def add_product_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != int(ADMIN_ID):
        update.message.reply_text("У вас нет прав для добавления товаров.")
        return ConversationHandler.END

    context.user_data['new_product_name'] = update.message.text
    update.message.reply_text("Введите цену товара:")
    return PRICE

async def add_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != int(ADMIN_ID):
        update.message.reply_text("У вас нет прав для добавления товаров.")
        return ConversationHandler.END

    try:
        price = int(update.message.text)
        context.user_data['new_product_price'] = price
        update.message.reply_text("Введите доступные размеры через запятую (например: XS,S,M,L,XL):")
        return SIZES
    except ValueError:
        update.message.reply_text("Пожалуйста, введите корректную цену (целое число).")
        return PRICE

async def add_product_sizes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != int(ADMIN_ID):
        update.message.reply_text("У вас нет прав для добавления товаров.")
        return ConversationHandler.END

    sizes = [size.strip() for size in update.message.text.split(',')]
    context.user_data['new_product_sizes'] = sizes
    update.message.reply_text("Введите доступные цвета через запятую (например: белый,черный,серый):")
    return COLORS

async def add_product_colors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != int(ADMIN_ID):
        update.message.reply_text("У вас нет прав для добавления товаров.")
        return ConversationHandler.END

    colors = [color.strip() for color in update.message.text.split(',')]
    context.user_data['new_product_colors'] = colors
    update.message.reply_text("Загрузите фотографию товара:")
    return PHOTO

async def add_product_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != int(ADMIN_ID):
        update.message.reply_text("У вас нет прав для добавления товаров.")
        return ConversationHandler.END

    photo_file = update.message.photo[-1].get_file()
    
    # Генерируем уникальное имя файла
    products = load_products()
    product_id = str(len(products) + 1)
    filename = f"product_{product_id}_0.jpg"
    filepath = os.path.join(WEBAPP_IMAGES_DIR, filename)
    
    photo_file.download(filepath)

    # Создаем новый товар
    new_product = {
        "id": product_id,
        "name": context.user_data.get('new_product_name', 'Без названия'),
        "description": context.user_data.get('new_product_description', 'Описание отсутствует'),
        "price": context.user_data.get('new_product_price', 0),
        "category": "Без категории",
        "sizes": context.user_data.get('new_product_sizes', []),
        "colors": context.user_data.get('new_product_colors', []),
        "images": [filename]
    }

    # Добавляем товар в список
    products.append(new_product)

    # Обновляем JSON файл
    save_products(products)

    update.message.reply_text("Товар успешно добавлен!")
    return ConversationHandler.END

async def delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить товар"""
    if update.effective_user.id != int(ADMIN_ID):
        await update.message.reply_text("У вас нет прав администратора.")
        return

    if not context.args:
        await update.message.reply_text("Укажите ID товара для удаления.\nПример: /delete_product 1")
        return

    product_id = context.args[0]
    products = load_products()
    
    # Находим товар для удаления
    product_index = None
    for i, product in enumerate(products):
        if product['id'] == product_id:
            product_index = i
            break

    if product_index is None:
        await update.message.reply_text(f"Товар с ID {product_id} не найден.")
        return

    # Удаляем изображения товара
    for image in products[product_index]['images']:
        try:
            os.remove(os.path.join(WEBAPP_IMAGES_DIR, image))
        except OSError:
            logger.warning(f"Не удалось удалить изображение: {image}")

    # Удаляем товар из списка
    products.pop(product_index)
    save_products(products)
    
    await update.message.reply_text(f"Товар с ID {product_id} успешно удален.")

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка данных от веб-приложения"""
    try:
        data = update.effective_message.web_app_data.data
        await update.message.reply_text(
            f"Спасибо за заказ!\n"
            f"Мы свяжемся с вами для подтверждения.\n"
            f"Данные заказа: {data}"
        )
    except Exception as e:
        logger.error(f"Error processing web app data: {e}")
        await update.message.reply_text("Произошла ошибка при обработке заказа.")

async def cart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия кнопки корзины"""
    query = update.callback_query
    await query.answer()
    
    # TODO: Реализовать функционал корзины
    await query.edit_message_text(
        "🛒 Корзина пока пуста. Выберите товары в каталоге!"
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет текущий процесс добавления товара"""
    await update.message.reply_text(
        "Добавление товара отменено. Если хотите начать заново, используйте /add_product."
    )
    return ConversationHandler.END

async def start_bot():
    """Функция для безопасного запуска бота"""
    try:
        # Проверяем корректность токена
        if not BOT_TOKEN or len(BOT_TOKEN.split(':')) != 2:
            logger.error("Некорректный токен бота")
            raise InvalidToken("Токен бота не соответствует формату")

        # Создаем Application
        application = (
            ApplicationBuilder()
            .token(BOT_TOKEN)
            .build()
        )

        # Принудительно удаляем webhook и все ожидающие обновления
        await application.bot.delete_webhook(drop_pending_updates=True)
        await asyncio.sleep(1)  # Даем время на обработку

        # Регистрируем обработчики команд
        application.add_handler(CommandHandler("start", retry_with_backoff()(start)))
        application.add_handler(CommandHandler("help", retry_with_backoff()(help_command)))
        application.add_handler(CommandHandler("list_products", retry_with_backoff()(list_products)))

        # Обработчики добавления товаров
        add_product_handler = ConversationHandler(
            entry_points=[CommandHandler('add_product', retry_with_backoff()(add_product))],
            states={
                TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, retry_with_backoff()(add_product_description))],
                DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, retry_with_backoff()(add_product_price))],
                PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, retry_with_backoff()(add_product_sizes))],
                SIZES: [MessageHandler(filters.TEXT & ~filters.COMMAND, retry_with_backoff()(add_product_colors))],
                COLORS: [MessageHandler(filters.TEXT & ~filters.COMMAND, retry_with_backoff()(add_product_photo))],
                PHOTO: [MessageHandler(filters.PHOTO, retry_with_backoff()(add_product_photo))]
            },
            fallbacks=[CommandHandler('cancel', retry_with_backoff()(cancel))]
        )
        application.add_handler(add_product_handler)

        # Обработчик данных от веб-приложения
        application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, retry_with_backoff()(handle_webapp_data)))

        # Обработчик корзины
        application.add_handler(CallbackQueryHandler(retry_with_backoff()(cart_callback), pattern='^cart$'))

        # Запускаем бота
        await application.initialize()
        await application.start()
        logger.info("Бот успешно запущен!")
        
        # Запускаем polling с небольшой задержкой
        await asyncio.sleep(1)
        await application.updater.start_polling(
            drop_pending_updates=True,
            timeout=30,
            allowed_updates=Update.ALL_TYPES
        )

    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    print(f"\nПолучен сигнал {signum}. Завершение работы...")
    sys.exit(0)

def main():
    # Устанавливаем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Сигнал завершения

    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print("\nБот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")

if __name__ == '__main__':
    main()
