from enum import IntEnum
from telegram.ext import ConversationHandler

class States(IntEnum):
    #главное меню
    START_MENU = 0
    MAIN_MENU = 1
    MAIN_MENU_HANDLER = 2
    CHAT_BOT = 3
    SERVICE_BOT = 4
    CONTRACT_BOT = 5
    

    TO_MAIN_MENU = 11
    
    
    #сервис и инсталляция
    SERVICE_TYPE = 20
    MANUFACTURER = 21
    MODEL = 22
    REGION = 23
    IF_UPDATE_MESSAGE = 24
    TO_TEXT_BOT = 25
    
    

    END = ConversationHandler.END
