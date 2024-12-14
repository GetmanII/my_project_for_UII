import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, ConversationHandler, filters, CallbackContext, CallbackQueryHandler
from classes.States import States

from config.answers_const_service import (
    entry_text, 
    choice_manufacturer_text,
    choice_model_text,
    choice_region_text,
    full_answer_text,
    answer_without_repair_text,
    answer_without_analysis_text,
    empty_service_answer,
    installation_answer_text,
    installation_none_answer_text,
    text_if_update_message,
    return_to_main_menu_text,
    empty_installation_answer,
    to_hardware_extractor_text,
    quit_extractor_text,
    confirm_model_from_extractor
    )

from config.answers_const_main import (
    transition_to_text_bot,   
)




service_xlsx = pd.read_excel('sheet_xlsx/service.xlsx')
installation_xlsx = pd.read_excel('sheet_xlsx/installation.xlsx')

def escape_markdown(text):

    """
    Escape special characters in a text string for MarkdownV2 parsing.

    This function takes a text string and escapes characters that have
    special meaning in MarkdownV2, ensuring that they are treated as 
    literal characters. It is useful for preparing text to be safely
    displayed in environments where MarkdownV2 is used, such as 
    Telegram messages.

    Args:
        text (str): The text string to escape.

    Returns:
        str: The escaped text string, with special characters prefixed
        by a backslash.
    """

    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text


async def remove_inline_keyboard(update: Update, context: CallbackContext):

    """
    Remove the inline keyboard from the last bot message
    
    Args:
        update: The Telegram update object
        context: The Telegram context object
    """
    
    last_message_id = context.user_data.get('last_bot_message_id')
    if last_message_id:
        try:
            await context.bot.edit_message_reply_markup(
                chat_id=update.effective_chat.id,
                message_id=last_message_id,
                reply_markup=None
            )
        except Exception as e:
            print(f"Error removing keyboard: {e}")
        

class ServiceInstallation:
    
    def __init__(self, service_xlsx: pd.DataFrame, installation_xlsx: pd.DataFrame):
        """
        Initializes the ServiceInstallation object.

        Args:
            service_xlsx (pd.DataFrame): The dataframe object of the 'service.xlsx' file.
            installation_xlsx (pd.DataFrame): The dataframe object of the 'installation.xlsx' file.
        """
        self.service_xlsx = service_xlsx
        self.installation_xlsx = installation_xlsx
    async def entry_point(self, update: Update, context: CallbackContext):

        """
        Handles the entry point of the service installation conversation.

        This function is called when the user selects the "Service" or "Installation" button in the main menu.
        It asks the user which service type they want to select.

        Args:
            update: The Telegram update object
            context: The Telegram context object

        Returns:
            States.SERVICE_TYPE
        """

        query = update.callback_query
        await query.answer()
        keyboard = [[InlineKeyboardButton('Разовые сервисы', callback_data='service')],
                    [InlineKeyboardButton('Инсталляция', callback_data='installation')],
                    [InlineKeyboardButton('В главное меню', callback_data='main_menu')]]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(entry_text, reply_markup=reply_markup, parse_mode='MarkdownV2')
        return States.SERVICE_TYPE

    async def if_update_message(self, update: Update, context: CallbackContext):

        """
        Handles the situation when the user sends a text message instead of selecting a button
        in the service installation conversation.

        This function is called when the user sends a text message while being in any of the
        service installation conversation states.

        Args:
            update: The Telegram update object
            context: The Telegram context object

        Returns:
            States.IF_UPDATE_MESSAGE
        """

        await remove_inline_keyboard(update, context)
        keyboard = [[InlineKeyboardButton('Нейро-консультант', callback_data='to_text_bot')],
                [InlineKeyboardButton('Остаться', callback_data='stay_service')],
                [InlineKeyboardButton('В главное меню', callback_data='main_menu')]]

        reply_markup = InlineKeyboardMarkup(keyboard)
        sent_message  = await update.message.reply_text(text_if_update_message, reply_markup=reply_markup, parse_mode='MarkdownV2')
        context.user_data['last_bot_message_id'] = sent_message.message_id
        return States.IF_UPDATE_MESSAGE
    
    async def return_to_main_menu(self, update: Update, context: CallbackContext):
        """
        Handles the transition to the main menu.

        This function is triggered when the user selects the "main menu" option.
        It updates the current message with a text guiding the user back to the 
        main menu and provides an inline keyboard with a button to confirm this 
        action.

        Args:
            update: The Telegram update object containing callback query.
            context: The Telegram context object with user data.

        Returns:
            States.END: The conversation state indicating the end of the current 
            interaction and return to the main menu.
        """
        query = update.callback_query
        await query.answer()
        keyboard = [[InlineKeyboardButton('В главное меню', callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        sent_message = await query.edit_message_text(return_to_main_menu_text, reply_markup=reply_markup, parse_mode='MarkdownV2')
        context.user_data['delete_message_id'] = sent_message.message_id
        return States.END
    

    




    async def handle_service_type(self, update: Update, context: CallbackContext):
            """
            Handles the service type selection.

            This function is triggered when the user selects a service type.
            It updates the current message with a text guiding the user to select
            a manufacturer and provides an inline keyboard with a button for each
            manufacturer in the service/installation data.

            Args:
                update: The Telegram update object containing callback query.
                context: The Telegram context object with user data.

            Returns:
                States.MANUFACTURER: The conversation state indicating that the
                user has selected a service type and should now select a
                manufacturer.
            """
            query = update.callback_query
            await query.answer()
            if 'from_hardware_extractor' not in context.user_data:
                context.user_data['service_type'] = query.data
            else:
                del context.user_data['from_hardware_extractor']     
            data = self.service_xlsx if context.user_data['service_type'] == 'service' else self.installation_xlsx
            manufacturers = pd.unique(data['Производитель']).tolist()
            reply_keyboard = [
                [InlineKeyboardButton(manufacturer, callback_data=f'{manufacturer}')] for manufacturer in manufacturers
            ] + [
                [InlineKeyboardButton('В главное меню', callback_data='main_menu')]
            ]

            markup = InlineKeyboardMarkup(reply_keyboard)
            await query.edit_message_text(choice_manufacturer_text, reply_markup=markup, parse_mode='MarkdownV2')
            return States.MANUFACTURER

    async def handle_manufacturer(self, update: Update, context: CallbackContext):
            """
            Handles the manufacturer selection process.

            This function is triggered when the user selects a manufacturer for their 
            equipment. It updates the user's data with the selected manufacturer and 
            presents a list of models associated with that manufacturer. An inline 
            keyboard is provided for the user to select a model or choose an alternative 
            action.

            Args:
                update: The Telegram update object containing callback query.
                context: The Telegram context object with user data.

            Returns:
                States.MODEL: The conversation state indicating that the user should 
                now select a model for the chosen manufacturer.
            """
            query = update.callback_query
            await query.answer()
            context.user_data['manufacturer_from_user'] = query.data
            data = self.service_xlsx if context.user_data['service_type'] == 'service' else self.installation_xlsx
            models = data[data['Производитель'] == context.user_data['manufacturer_from_user']]['Модель (category)'].tolist()
            reply_keyboard = [
                [InlineKeyboardButton(model, callback_data=f'{model}')] for model in models
                ] + [
                    [InlineKeyboardButton('В главное меню', callback_data='main_menu')]
                ]

            markup = InlineKeyboardMarkup(reply_keyboard)
            await query.edit_message_text(choice_model_text, reply_markup=markup, parse_mode='MarkdownV2')
            return States.MODEL

    async def handle_model(self, update: Update, context: CallbackContext):
            """
            Handles the model selection process.

            This function is triggered when the user selects a model for their chosen manufacturer.
            It updates the user's data with the selected model and presents a list of regions where
            the model can be installed. An inline keyboard is provided for the user to select a region
            or choose an alternative action.

            Args:
                update: The Telegram update object containing callback query.
                context: The Telegram context object with user data.

            Returns:
                States.END: The conversation state indicating that the user should now be presented
                with a cost summary for the chosen model
                States.REGION:  A conversation state indicating that the user should now be given a 
                choice of regions for the installation service, or alternatively, the user 
                should be given the option to return to the main menu.
            """
            query = update.callback_query
            await query.answer()
            if 'from_hardware_extractor' not in context.user_data:
                context.user_data['model_from_user'] = query.data
            else:
                del context.user_data['from_hardware_extractor']
                
            if context.user_data['service_type'] == 'service':
                await self.service_answer(update, context)
                return States.END
            else:
                regions = self.installation_xlsx.columns.tolist()[2:]
                keyboard = [
                    [InlineKeyboardButton(region, callback_data=f'{region}')] for region in regions
                ] + [[InlineKeyboardButton('В главное меню', callback_data='main_menu')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(choice_region_text, reply_markup=reply_markup, parse_mode='MarkdownV2')
                return States.REGION

    async def handle_region(self, update: Update, context: CallbackContext):
            """
            Handles the region selection process.

            This function is triggered when the user selects a region for the installation 
            service. It updates the user's data with the selected region and proceeds to 
            calculate and present the installation cost for the selected model and region.

            Args:
                update: The Telegram update object containing callback query.
                context: The Telegram context object with user data.

            Returns:
                States.END: The conversation state indicating the end of the current 
                interaction after presenting the installation cost.
            """
            query = update.callback_query
            await query.answer()
            context.user_data['region_from_user'] = query.data
            await self.installation_answer(update, context)
            return States.END

    async def service_answer(self, update: Update, context: CallbackContext):
        """
        Handles the service answer process.

        This function is triggered when the user selects a model for the service type.
        It checks if the selected model is in the list of supported models and if so, 
        calculates and presents the cost for the selected model.

        Args:
            update: The Telegram update object containing callback query.
            context: The Telegram context object with user data.

        Returns:
            None
        """
        models = self.service_xlsx['Модель (category)'].tolist()
        if context.user_data['model_from_user']  in models:
            
            cost_repair = self.service_xlsx.loc[
                (self.service_xlsx['Модель (category)'] == context.user_data['model_from_user']),
                'Стоимость услуги 1'].values[0]
            cost_analysis = self.service_xlsx.loc[
                (self.service_xlsx['Модель (category)'] == context.user_data['model_from_user']),
                'Стоимость услуги 2'].values[0]

            if cost_repair != '-' and cost_analysis != '-':
                answer_text = full_answer_text.format(model_from_user = escape_markdown(context.user_data['model_from_user']),
                                                    
                                                    cost_repair = cost_repair,
                                                    cost_analysis = cost_analysis)
            elif cost_repair == '-' and cost_analysis != '-':
                answer_text = answer_without_repair_text.format(model_from_user = escape_markdown(context.user_data['model_from_user']),
                                                    
                                                    cost_analysis = cost_analysis)
            elif cost_analysis == '-' and cost_repair != '-':
                answer_text = answer_without_analysis_text.format(model_from_user = escape_markdown(context.user_data['model_from_user']),
                                                    
                                                    cost_repair = cost_repair)
            else:
                answer_text = empty_service_answer
                
        else:
            answer_text = empty_service_answer
        keyboard = [
            [InlineKeyboardButton('В главное меню', callback_data=f'main_menu')], 
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        sent_message = await update.callback_query.edit_message_text(answer_text, reply_markup=reply_markup, parse_mode='MarkdownV2')
        context.user_data['last_bot_message_id'] = sent_message.message_id

    async def installation_answer(self, update: Update, context: CallbackContext):
        """
        Handles the installation answer step in the service installation conversation.

        This function is called after the user has selected a region for the installation
        of their equipment. The function gets the cost of installation from the Excel
        spreadsheet and formats the answer text accordingly. If the cost of installation
        is not available, it returns a message indicating that the installation is not
        supported in the selected region.

        Args:
            update: The Telegram update object containing callback query.
            context: The Telegram context object with user data.

        Returns:
            None
        """
        models = self.installation_xlsx['Модель (category)'].tolist()
        if context.user_data['model_from_user']  in models:
            
            cost_installation = self.installation_xlsx.loc[
                (self.installation_xlsx['Модель (category)'] == context.user_data['model_from_user']),
                context.user_data['region_from_user']].values[0]
            if cost_installation == '-':
                answer_text = installation_none_answer_text.format(model_from_user = escape_markdown(context.user_data['model_from_user']),
                                                        
                                                        region_from_user = escape_markdown(context.user_data['region_from_user']))
            else:
                answer_text = installation_answer_text.format(model_from_user = escape_markdown(context.user_data['model_from_user']),
                                                        
                                                        region_from_user = escape_markdown(context.user_data['region_from_user']),
                                                        cost_installation = cost_installation)
                
        else:
            answer_text = empty_installation_answer
        keyboard = [
            [InlineKeyboardButton('В главное меню', callback_data=f'main_menu')], 
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        sent_message = await update.callback_query.edit_message_text(answer_text, reply_markup=reply_markup, parse_mode='MarkdownV2')
        context.user_data['last_bot_message_id'] = sent_message.message_id
        
    async def update_message_handler(self, update: Update, context: CallbackContext):
        """
        Handles the situation when the user sends a text message or clicks the "main menu" button after if_update_message function.

        Args:
            update: The Telegram update object containing callback query.
            context: The Telegram context object with user data.

        Returns:
            The next conversation state, either States.END if the user clicks the "main menu" button or States.TO_TEXT_BOT if the user sends a text message.
        """
        keyboard = [
            [InlineKeyboardButton('В главное меню', callback_data = 'main_menu')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)       
        if update.message:
            await remove_inline_keyboard(update, context)
            sent_message = await update.message.reply_text(transition_to_text_bot, reply_markup=reply_markup, parse_mode='MarkdownV2')
            context.user_data['last_bot_message_id'] = sent_message.message_id
            return States.TO_TEXT_BOT
        else:
            query = update.callback_query
            await query.answer()
            if query.data == 'to_text_bot':
                await query.edit_message_text(transition_to_text_bot, reply_markup=reply_markup, parse_mode='MarkdownV2')
                return States.TO_TEXT_BOT
            else:
                return await self.entry_point(update, context)
            


service_bot = ServiceInstallation(service_xlsx, installation_xlsx)
service_conversation_handler =  ConversationHandler(
            entry_points=[
                          CallbackQueryHandler(service_bot.return_to_main_menu, pattern='main_menu'),
                          CallbackQueryHandler(service_bot.entry_point),
                          MessageHandler(filters.TEXT & ~filters.COMMAND, service_bot.if_update_message)
                          ],
            states={
                States.SERVICE_TYPE: [
                                      CallbackQueryHandler(service_bot.return_to_main_menu, pattern='main_menu'),
                                      CallbackQueryHandler(service_bot.handle_service_type),
                                      MessageHandler(filters.TEXT & ~filters.COMMAND, service_bot.if_update_message)
                                      ],
                States.MANUFACTURER: [
                                      CallbackQueryHandler(service_bot.return_to_main_menu, pattern='main_menu'),
                                      CallbackQueryHandler(service_bot.handle_manufacturer),                                    
                                      MessageHandler(filters.TEXT & ~filters.COMMAND, service_bot.if_update_message)
                                      ],
                States.MODEL: [
                                      CallbackQueryHandler(service_bot.return_to_main_menu, pattern='main_menu'),
                                      CallbackQueryHandler(service_bot.handle_model),
                                      MessageHandler(filters.TEXT & ~filters.COMMAND, service_bot.if_update_message)
                                      ],
                States.REGION: [
                                      CallbackQueryHandler(service_bot.return_to_main_menu, pattern='main_menu'),
                                      CallbackQueryHandler(service_bot.handle_region),
                                      MessageHandler(filters.TEXT & ~filters.COMMAND, service_bot.if_update_message)
                                      ],
                States.IF_UPDATE_MESSAGE: [
                                      CallbackQueryHandler(service_bot.return_to_main_menu, pattern='main_menu'),
                                      CallbackQueryHandler(service_bot.update_message_handler),
                                      MessageHandler(filters.TEXT & ~filters.COMMAND, service_bot.update_message_handler)
                                      ],
                },
            fallbacks=[],
            map_to_parent={
                States.END: States.MAIN_MENU,
                States.TO_TEXT_BOT: States.CHAT_BOT,
                }
           )