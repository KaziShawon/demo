import os
import json
import requests
import streamlit as st
from typing import Optional
from dotenv import load_dotenv
from unidecode import unidecode
from streamlit_chat import message
from pydantic import BaseModel, Field

load_dotenv()

def generate_response(user_input):
    
    _url_message = 'https://api.wit.ai/message'
    _header = {'Authorization': f'Bearer {os.getenv("WitKey")}'}
    resp = requests.get(f"{_url_message}?v=20230215&q={unidecode(user_input)}", headers=_header)
    data = json.loads(resp.content)

    return data['intents'], data['entities']

class ConversationHistory(BaseModel):
    past_user_inputs: Optional[list[str]] = []
    generated_responses: Optional[list[str]] = []
    user_input: str = Field(example="¿Hola, cómo estás?")

def witai_response(history: ConversationHistory) -> str:
    # Step 0: Receive the API payload as a dictionary
    history = dict(history)

    # Step 1: Initialize the conversation history
    past_user_inputs=history["past_user_inputs"],
    generated_responses=history["generated_responses"],

    # Step 2: Get the intents and entites from wit.ai
    intents, entities = generate_response(history["user_input"])

    try:
        intent = intents[0]['name']
    except:
        intent = "No se encontró ninguna intención"
    # Step 3: Return the intents
    return intent

# --------------------------------------------------------------------------------------------------------
# ------------------------------------------ StreamLit ---------------------------------------------------
# --------------------------------------------------------------------------------------------------------

def clear_conversation():
    """
    Clear all the stored session_state variables in the
    Streamlit frontend
    """
    if (
        st.button("🧹 Clear conversation", use_container_width=True)
        or "conversation_history" not in st.session_state
    ):
        st.session_state.conversation_history = {
            "past_user_inputs": [],
            "generated_responses": [],
        }
        st.session_state.user_input = ""
        st.session_state.interleaved_conversation = []


def display_conversation(conversation_history):
    """
    Create a chat interface with streamlit_chat library.
    """

    st.session_state.interleaved_conversation = []

    for idx, (human_text, ai_text) in enumerate(
        zip(
            reversed(conversation_history["past_user_inputs"]),
            reversed(conversation_history["generated_responses"]),
        )
    ):
        # Display the messages on the frontend
        message(ai_text, is_user=False, key=f"ai_{idx}")
        message(human_text, is_user=True, key=f"human_{idx}")

        # Store the messages in a list for download
        st.session_state.interleaved_conversation.append([False, ai_text])
        st.session_state.interleaved_conversation.append([True, human_text])

@st.cache_data()
def microservice_response(user_input):
    """Send the user input to the LLM API and return the response."""
    payload = st.session_state.conversation_history
    payload["user_input"] = user_input
    # print(f"Payload: {payload}")

    response = witai_response(payload)

    # Manually add the user input and generated response to the conversation history
    st.session_state.conversation_history["past_user_inputs"].append(user_input)
    st.session_state.conversation_history["generated_responses"].append(response)

def main():
    st.title("Microservices ChatBot App")

    col1, col2 = st.columns(2)
    with col1:
        clear_conversation()
    
    # Get user input
    if user_input := st.text_input("Haz tu pregunta 👇", key="user_input"):
        microservice_response(user_input)

    # Display the entire conversation on the frontend
    display_conversation(st.session_state.conversation_history)


if __name__ == "__main__":
    main()