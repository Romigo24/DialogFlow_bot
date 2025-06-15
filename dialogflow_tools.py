from google.cloud import dialogflow


def get_dialogflow_response(text, session_id, dialogflow_project_id, language_code='ru'):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(dialogflow_project_id, session_id)

    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(
        request={"session": session, "query_input": query_input}
    )

    if not response.query_result.intent.is_fallback:
        return None
    return response.query_result.fulfillment_text