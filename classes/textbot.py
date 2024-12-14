import os
from openai import AsyncOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from classes.service_installation import remove_inline_keyboard


from classes.States import States

from config.prompts_config import (
    system_company,
    user_company,
)

from config.answers_const_main import (
    from_text_bot_to_main,
)


load_dotenv()

MAX_MESSAGE_LENGTH = 4096

api_key = os.environ.get("OPENAI_VSEAPI_KEY")
# api_key = os.environ.get("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = api_key

client = AsyncOpenAI(base_url="https://api.vsegpt.ru/v1") ################################################################# убрать переадресацию

embeddings = OpenAIEmbeddings(model='text-embedding-3-large', openai_api_base = "https://api.vsegpt.ru/v1/") ################################################################### убрать переадресацию
db_path = os.path.join('db')
db_main = FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization = True)

model_gpt = 'openai/gpt-4o-mini' #####################################################################  


# client = AsyncOpenAI() 

# embeddings = OpenAIEmbeddings(model='text-embedding-3-large') 
# db_path = os.path.join('db')
# db_main = FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization = True)

# model_gpt = 'gpt-4o' 

async def company_answer(system, user, topic, db, chat_history, num_chunks, model, temperature):
    """
    Async function that makes an AI answer to the user's message based on the company's knowledge base.

    Args:
        system (str): The company's prompt.
        user (str): The user's prompt.
        topic (str): The text of the user's message.
        db (FAISS): The vectorstore that contains the company's knowledge base.
        chat_history (str): The text of the user's previous messages.
        num_chunks (int): The number of chunks to use for the search.
        model (str): The model to use for the completion.
        temperature (float): The temperature to use for the completion.

    Returns:
        str: The AI's answer to the user's message based on the company's knowledge base.
    """
    docs = await db.asimilarity_search(topic, num_chunks)
    message_content = '\n'.join([f'{"-" * 50}\n{doc.page_content}' for doc in docs])
    user = user.format(
        topic=topic,
        message_content=message_content,
        chat_history=chat_history
    )
    messages = [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': user}
    ]
    completion = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    answer = completion.choices[0].message.content
    return answer


async def get_answer(topic, chat_history, num_chunks, temperature):
    
    """
    Async function that makes an AI answer to the user's message based on the company's knowledge base.

    Args:
        topic (str): The text of the user's message.
        chat_history (list): The list of dictionaries that contain the user's previous messages and the AI's answers.
        num_chunks (int): The number of chunks to use for the search.
        temperature (float): The temperature to use for the completion.

    Returns:
        str: The AI's answer to the user's message based on the company's knowledge base.
    """
    if chat_history:
        # Извлекаем последние 4 словаря
        last_messages = chat_history[-4:]  
        # Формируем список строк для каждой пары вопрос-ответ
        history_list = [f"Вопрос клиента: {msg['Вопрос клиента']}, Ответ нейроконсультанта: {msg['Ответ нейроконсультанта']}" for msg in last_messages]
        
        # Объединяем их в одну строку, если нужно
        last_four_messages = "\n".join(history_list)
    else:
        last_four_messages = ""
        
    main_answer = await company_answer(system_company, user_company, topic, db_main, last_four_messages, num_chunks, model_gpt, temperature)
    chat_history.append({'Вопрос клиента': topic, 'Ответ нейроконсультанта': main_answer})
    return main_answer 




async def text_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Async function that is called when the user sends a text message to the bot or clicks the "main menu" button.

    Args:
        update: The Telegram update object.
        context: The Telegram context object.

    Returns:
        States.CHAT_BOT if the user sends a text message, States.MAIN_MENU if the user clicks the "main menu" button.
    """
    if update.message:
        logging.info("text_bot вызван")
        await remove_inline_keyboard(update, context)
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        main_answer= await get_answer(update.message.text, context.user_data['chat_history'], num_chunks=5, temperature=0.1) 
        message = main_answer
        keyboard = [
            [InlineKeyboardButton('В главное меню', callback_data = 'main_menu')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if len(message) > MAX_MESSAGE_LENGTH:
        # Разбить сообщение на части
            parts = [message[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(message), MAX_MESSAGE_LENGTH)]
            for i, part in enumerate(parts):
                if i == len(parts) - 1:  # Для последней части добавляем кнопку
                    sent_message = await update.message.reply_text(part, reply_markup=reply_markup)
                    context.user_data['last_bot_message_id'] = sent_message.message_id
                else:
                    await update.message.reply_text(part)
        else:
            sent_message = await update.message.reply_text(message, reply_markup=reply_markup)
            context.user_data['last_bot_message_id'] = sent_message.message_id
        return States.CHAT_BOT
    else:
        query = update.callback_query
        await query.answer()
        await remove_inline_keyboard(update, context)
        keyboard = [
            [InlineKeyboardButton('В главное меню', callback_data = 'main_menu')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)        
        sent_message = await query.message.reply_text(from_text_bot_to_main, reply_markup=reply_markup, parse_mode='MarkdownV2')
        context.user_data['delete_message_id'] = sent_message.message_id
        return States.MAIN_MENU
