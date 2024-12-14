import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, filters, CallbackContext, CallbackQueryHandler
from dotenv import load_dotenv
import os


from classes.service_installation import service_conversation_handler, remove_inline_keyboard
from classes.textbot import text_bot


from classes.States import States
from config.answers_const_main import (
    start_text,
    transition_to_service_bot,
    transition_to_text_bot,
    main_menu_text,
    instead_button_text,
)


load_dotenv()

# загружаем токен бота
TOKEN = os.environ.get("TOKEN")

logging.getLogger('httpx').setLevel(logging.WARNING)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


async def start(update, context):
    """
    Entry point for the bot.

    Handles the initial message sent to the bot and displays the main menu
    with three options: "Нейро-консультант", "Разовые сервисы / Инсталляция",
    and "Контрактная поддержка".

    Args:
        update (Update): The Telegram update object.
        context (ContextTypes.DEFAULT_TYPE): The Telegram context object.

    Returns:
        States.MAIN_MENU_HANDLER: The conversation state indicating the start of the
        main menu.
    """

    logging.info("start вызван")
    context.user_data['chat_history'] = []
    keyboard = [
        [InlineKeyboardButton("Нейро-консультант", callback_data='chat_bot')],
        [InlineKeyboardButton("Разовые сервисы / Инсталляция", callback_data='service_bot')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    sent_message = await update.message.reply_text(
        start_text,
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )
    context.user_data['last_bot_message_id'] = sent_message.message_id
    return States.MAIN_MENU_HANDLER


async def service_start(update: Update, context: CallbackContext) -> int:
    """
    Handles the transition to the service start menu.

    This function is triggered when the user selects the "service" option.
    It updates the current message with a text guiding the user to the service
    menu and provides an inline keyboard with options to start the service or
    return to the main menu.

    Args:
        update: The Telegram update object containing callback query.
        context: The Telegram context object with user data.

    Returns:
        The next conversation state, typically indicating the transition to
        the service start menu.
    """
    query = update.callback_query
    await query.answer()
    keyboard = [
    [InlineKeyboardButton('Начать', callback_data='service_start')],
    [InlineKeyboardButton('В главное меню', callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text( 
        transition_to_service_bot,
        reply_markup=reply_markup,
        parse_mode='MarkdownV2')



    


        
async def main_menu(update: Update, context: CallbackContext) -> int:
    """
    Handles the transition to the main menu.

    This function is triggered when the user selects the "main menu" option.
    It updates the current message with a text guiding the user to the main
    menu and provides an inline keyboard with options to start the service
    or return to the contract menu.

    Args:
        update: The Telegram update object containing callback query.
        context: The Telegram context object with user data.

    Returns:
        The next conversation state, typically indicating the transition to
        the main menu.
    """
    logging.info("main_menu вызван")
    query = update.callback_query
    await query.answer()
    await remove_inline_keyboard(update, context)
    if 'delete_message_id' in context.user_data:
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=context.user_data['delete_message_id'])
        del context.user_data['delete_message_id']
    keyboard = [
        [InlineKeyboardButton("Нейро-консультант", callback_data='chat_bot')],
        [InlineKeyboardButton("Разовые сервисы / Инсталляция", callback_data='service_bot')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    sent_message = await query.message.reply_text(
        main_menu_text,
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )
    context.user_data['last_bot_message_id'] = sent_message.message_id
    return States.MAIN_MENU_HANDLER

async def main_menu_handler(update: Update, context: CallbackContext) -> int:
    """
    Handles the user's selection from the main menu.

    This function responds to the user's choice from the main menu options
    and transitions to the appropriate bot mode: chat, service, or contract.
    It updates the current message with relevant information and provides
    inline keyboard options as necessary.

    Args:
        update: The Telegram update object containing callback query.
        context: The Telegram context object with user data.

    Returns:
        The next conversation state, indicating the transition to one of the
        bot modes: States.CHAT_BOT, States.SERVICE_BOT, or States.CONTRACT_BOT.
    """
    query = update.callback_query
    await query.answer()
    logging.info(f"Нажата кнопка: {query.data}")
    if query.data == 'chat_bot':
        logging.info("Переход в режим чата")
        keyboard = [
            [InlineKeyboardButton('В главное меню', callback_data = 'main_menu')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(transition_to_text_bot, reply_markup=reply_markup, parse_mode='MarkdownV2')
        return States.CHAT_BOT
    elif query.data == 'service_bot':
        logging.info("Переход в режим сервиса")
        await service_start(update, context)
        return States.SERVICE_BOT


    
async def text_instead_button(update: Update, context: CallbackContext):
    """
    Handles the situation when the user sends a text message instead of selecting a button
    in the start menu.

    This function is called when the user sends a text message while being in the start menu.
    It responds with a message guiding the user to use the keyboard and ignores the message.

    Args:
        update: The Telegram update object
        context: The Telegram context object with user data

    Returns:
        None
    """
    logging.info("text_not_button вызван")
    # Игнорируем любые текстовые сообщения от пользователя
    await update.message.reply_text(instead_button_text, parse_mode='MarkdownV2')


        

def main():

    # точка входа в приложение
    """
    Entry point of the application.

    Builds the Application object and its conversation handlers, then starts the bot.

    :return: None
    """

    application = Application.builder().token(TOKEN).concurrent_updates(True).build()
    print('Бот запущен...')


    # Обработчик для главного меню
    main_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start),
                      MessageHandler(filters.TEXT&~filters.COMMAND, start)],
        states={
            States.MAIN_MENU: [CallbackQueryHandler(main_menu),
                                MessageHandler(filters.TEXT&~filters.COMMAND, text_instead_button)],
            States.MAIN_MENU_HANDLER: [CallbackQueryHandler(main_menu_handler),
                                MessageHandler(filters.TEXT&~filters.COMMAND, text_instead_button)],
            States.CHAT_BOT: [MessageHandler(filters.TEXT&~filters.COMMAND, text_bot),
                              CallbackQueryHandler(text_bot)],
            States.SERVICE_BOT: [service_conversation_handler],

        },
        
        fallbacks=[],
    )

    application.add_handler(main_handler)



    application.run_polling()



if __name__ == "__main__":
    main()