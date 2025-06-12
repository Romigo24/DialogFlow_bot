import os
import random
import logging
from dotenv import load_dotenv
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from google.cloud import dialogflow



logger = logging.getLogger(__file__)


def send_error_to_telegram(error_message, tg_token, admin_chat_id):
    bot = Bot(token=tg_token)
    bot.send_message(chat_id=admin_chat_id, text=f"❗ Ошибка: {error_message}")

def initialize_dialogflow(project_id):
    return dialogflow.SessionsClient()


def detect_intent(session_client, project_id, session_id, text, language_code='ru'):
    session = session_client.session_path(project_id, session_id)
    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(
        request={'session': session, 'query_input': query_input}
    )

    if response.query_result.intent.is_fallback:
        return None
    return response.query_result.fulfillment_text


def initialize_vk_bot(vk_token):
    vk_session = vk_api.VkApi(token=vk_token)
    vk = vk_session.get_api()
    longpool = VkLongPoll(vk_session)
    return vk, longpool


def send_message(vk_client, user_id, text):
    vk_client.messages.send(
        user_id=user_id,
        message=text,
        random_id=random.randint(1, 1000)
    )


def main():
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    load_dotenv()

    vk_group_token = os.environ['VK_BOT_TOKEN']
    dialogflow_project_id = os.environ['DIALOGFLOW_PROJECT_ID']
    tg_token = os.environ['TELEGRAM_BOT_TOKEN']
    admin_chat_id = os.environ['ADMIN_CHAT_ID']

    try:
        dialogflow_client = initialize_dialogflow(dialogflow_project_id)
        vk_client, longpoll = initialize_vk_bot(vk_group_token)
        logger.info("Бот запущен")

        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                try:
                    response_text = detect_intent(
                        dialogflow_client,
                        dialogflow_project_id,
                        str(event.user_id),
                        event.text,
                        language_code='ru'
                    )

                    if response_text:
                        send_message(vk_client, event.user_id, response_text)

                except Exception as e:
                    send_message(vk_client, event.user_id, 'Произошла ошибка :(')
                    logger.error(f'Ошибка: {str(e)}')

    except Exception as e:
        logger.critical(f'Критическая ошибка при инициализации бота: {str(e)}')
        send_error_to_telegram(f'VK Bot CRASHED: {e}', tg_token, admin_chat_id)

if __name__ == '__main__':
    main()