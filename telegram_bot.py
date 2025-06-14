import os
import logging
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from google.cloud import dialogflow
from google.api_core.exceptions import GoogleAPICallError, InvalidArgument
from dotenv import load_dotenv


logger = logging.getLogger(__name__)


def send_error_to_telegram(error_message, tg_token, admin_chat_id):
    bot = Bot(token=tg_token)
    bot.send_message(chat_id=admin_chat_id, text=f"❗ Ошибка: {error_message}")


def start(update, context):
    update.message.reply_text(f'Привет, {update.effective_user.first_name}!\n'
            'Я умный бот, напиши мне что-нибудь, и я отвечу через DialogFlow!'
            )


def get_dialogflow_response(text, session_id, dialogflow_project_id, language_code='ru'):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(dialogflow_project_id, session_id)

    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(
        request={"session": session, "query_input": query_input}
    )

    return response.query_result.fulfillment_text


def handle_message(update, context):
    try:
        user_message = update.message.text
        session_id = f'tg-{update.effective_user.id}'
        dialogflow_project_id = context.bot_data['dialogflow_project_id']

        dialogflow_response = get_dialogflow_response(user_message, session_id, dialogflow_project_id)

        update.message.reply_text(dialogflow_response)

    except (GoogleAPICallError, InvalidArgument) as e:
        logger.warning("Ошибка при обращении к DialogFlow: %s", e)
        update.message.reply_text("Ой, я не могу сейчас ответить. Попробуй позже.")
        send_error_to_telegram(str(e), context.bot.token, context.bot_data['admin_chat_id'])
    except Exception as e:
        logger.exception("Неизвестная ошибка:")
        update.message.reply_text("Что-то пошло не так. Напиши позже!")
        send_error_to_telegram(str(e), context.bot.token, context.bot_data['admin_chat_id'])


def error_handler(update, context):
    logger.exception('Update "%s" caused error "%s"', update, context.error)
    send_error_to_telegram(str(context.error), context.bot.token, context.bot_data['admin_chat_id'])


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    load_dotenv()

    tg_token = os.environ['TELEGRAM_BOT_TOKEN']
    dialogflow_project_id = os.environ['DIALOGFLOW_PROJECT_ID']
    admin_chat_id = os.environ['ADMIN_CHAT_ID']

    updater = Updater(tg_token)
    dispatcher = updater.dispatcher
    dispatcher.bot_data['dialogflow_project_id'] = dialogflow_project_id
    dispatcher.bot_data['admin_chat_id'] = admin_chat_id

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dispatcher.add_error_handler(error_handler)

    updater.start_polling()
    logger.info("Bot started with DialogFlow integration")
    updater.idle()


if __name__ == '__main__':
    main()