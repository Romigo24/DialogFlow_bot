import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from google.cloud import dialogflow
from dotenv import load_dotenv


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()


DIALOGFLOW_PROJECT_ID = os.getenv('DIALOGFLOW_PROJECT_ID')
LANGUAGE_CODE = 'ru'

def start(update, context):
    update.message.reply_text('Привет! Я теперь использую DialogFlow для ответов.')

def get_dialogflow_response(text, session_id):
    try:
        session_client = dialogflow.SessionsClient()
        session = session_client.session_path(DIALOGFLOW_PROJECT_ID, session_id)

        text_input = dialogflow.TextInput(text=text, language_code=LANGUAGE_CODE)
        query_input = dialogflow.QueryInput(text=text_input)

        response = session_client.detect_intent(
            session=session,
            query_input=query_input
        )

        return response.query_result.fulfillment_text

    except Exception as e:
        logger.error(f"DialogFlow error: {e}")
        return "Извините, произошла ошибка при обработке запроса."

def handle_message(update, context) -> None:
    try:
        user_message = update.message.text
        user_id = update.message.from_user.id

        dialogflow_response = get_dialogflow_response(user_message, str(user_id))

        update.message.reply_text(dialogflow_response)

    except Exception as e:
        logger.error(f"Telegram bot error: {e}")
        update.message.reply_text("Произошла ошибка при обработке сообщения.")

def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(f'Update {update} caused error {context.error}')

def main():
    updater = Updater(os.getenv('TELEGRAM_BOT_TOKEN'))

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dispatcher.add_error_handler(error_handler)

    updater.start_polling()
    logger.info("Bot started with DialogFlow integration")
    updater.idle()

if __name__ == '__main__':
    main()