import os
import random
from dotenv import load_dotenv
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from google.cloud import dialogflow


def initialize_dialogflow(project_id):
    return dialogflow.SessionsClient()


def detect_intent(session_client, project_id, session_id, text, language_code='ru'):
    session = session_client.session_path(project_id, session_id)
    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(
        request={'session': session, 'query_input': query_input}
    )
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
        random_id=0
    )


def main():
    load_dotenv()

    vk_token = os.getenv('VK_BOT_TOKEN')
    DIALOGFLOW_PROJECT_ID = os.getenv('DIALOGFLOW_PROJECT_ID')
    LANGUAGE_CODE = 'ru'

    try:
        dialogflow_client = initialize_dialogflow(DIALOGFLOW_PROJECT_ID)
        vk_client, longpoll = initialize_vk_bot(vk_token)
        print('Умный бот запущен и готов к общению...')

        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                try:
                    response_text = detect_intent(
                        dialogflow_client,
                        DIALOGFLOW_PROJECT_ID,
                        str(event.user_id),
                        event.text,
                        LANGUAGE_CODE
                    )

                    send_message(vk_client, event.user_id, response_text)

                except Exception as e:
                    error_msg = 'Произошла ошибка при обработке вашего сообщения'
                    send_message(vk_client, event.user_id, error_msg)
                    print(f'Ошибка: {str(e)}')

    except Exception as e:
        print(f'Критическая ошибка при инициализации бота: {str(e)}')

if __name__ == '__main__':
    main()