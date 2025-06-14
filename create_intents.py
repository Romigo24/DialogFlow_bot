import json
import os
from dotenv import load_dotenv
from google.cloud import dialogflow
from google.api_core.exceptions import GoogleAPICallError


def create_intent(project_id, display_name, training_phrases_parts, message_texts):
    intents_client = dialogflow.IntentsClient()

    parent = dialogflow.AgentsClient.agent_path(project_id)
    training_phrases = []

    for training_phrases_part in training_phrases_parts:
        part = dialogflow.Intent.TrainingPhrase.Part(text=training_phrases_part)
        training_phrase = dialogflow.Intent.TrainingPhrase(parts=[part])
        training_phrases.append(training_phrase)

    text = dialogflow.Intent.Message.Text(text=message_texts)
    message = dialogflow.Intent.Message(text=text)

    intent = dialogflow.Intent(
        display_name=display_name,
        training_phrases=training_phrases,
        messages=[message]
    )

    response = intents_client.create_intent(
        request={'parent': parent, 'intent': intent}
    )
    return response


def main():
    load_dotenv()

    project_id = os.getenv('DIALOGFLOW_PROJECT_ID')

    try:
        with open('training_questions.json', 'r', encoding='utf=8') as f:
            training_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f'Ошибка при чтении файла: {e}')
        return
    
    for intent_name, data in training_data.items():
        phrases = data.get('questions', [])
        answer = data.get('answer', '')

        if not phrases or not answer:
            print(f'Пропускаем intent "{intent_name}" - отсутствуют фразы или ответ')
            continue

        print(f'\nСоздаём intent: {intent_name}')
        print(f'Количество фраз: {len(phrases)}')
        print(f'Ответ: {answer[:50]}...')

        try:
            create_intent(project_id, intent_name, phrases, [answer])
            print(f'Intent "{intent_name}" успешно создан')
        except (GoogleAPICallError, ValueError) as e:
            print(f'Ошибка при создании intent "{intent_name}": {e}')


if __name__=='__main__':
    main()