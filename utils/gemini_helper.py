# utils/gemini_helper.py
# Handles all communication with Gemini API using the google-genai SDK

import os
import streamlit as st # type: ignore
# pyrefly: ignore [missing-import]
from google import genai


# Configuration — change model name here
MODEL_NAME = "gemini-2.5-flash"


def load_env_file():
    """Load key-value pairs from .env if it exists in the current directory."""
    if os.path.exists(".env"):
        try:
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip().strip('"').strip("'")
        except Exception:
            pass


def get_api_key() -> str:
    """
    Retrieve Gemini API Key from environment or streamlit session state.
    """
    # Load .env file if available
    load_env_file()

    # 1. Check environment variable
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return api_key

    # 2. Check Streamlit session state
    if "gemini_api_key" in st.session_state:
        return st.session_state.gemini_api_key

    return ""


def get_client() -> genai.Client | None:
    """
    Create and return a configured Gemini Client.
    Returns None if no API key is available.
    """
    api_key = get_api_key()
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


def generate_response(prompt: str) -> str:
    """
    Generate a single response from Gemini given a plain prompt string.
    Returns the full response text or an error message.
    """
    client = get_client()
    if not client:
        return (
            " Gemini API Key not found. Please set the `GEMINI_API_KEY` environment variable "
            "or enter it in the sidebar."
        )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f" Error connecting to Gemini API: {str(e)}"


def generate_chat_response(system_prompt: str, user_message: str) -> str:
    """
    Generate a chat response with a system prompt and user message.
    """
    client = get_client()
    if not client:
        return (
            " Gemini API Key not found. Please set the `GEMINI_API_KEY` environment variable "
            "or enter it in the sidebar."
        )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_message,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
        )
        return response.text
    except Exception as e:
        return f" Error connecting to Gemini API: {str(e)}"


def stream_response(prompt: str):
    """
    Generator that streams tokens one by one from Gemini.
    Designed for use with Streamlit's st.write_stream().
    """
    client = get_client()
    if not client:
        yield " Gemini API Key not found. Please provide an API key."
        return

    try:
        response = client.models.generate_content_stream(
            model=MODEL_NAME,
            contents=prompt,
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f" Error: {str(e)}"


def check_gemini_connection() -> tuple[bool, str]:
    """
    Check if Gemini is accessible and the API key is valid.
    Returns (success: bool, message: str).
    """
    client = get_client()
    if not client:
        return False, "Gemini API Key is missing. Please configure it in the environment or sidebar."

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents="Say 'OK' in one word.",
        )
        if response.text:
            return True, f"Connected to Gemini API successfully with model `{MODEL_NAME}`"
        return False, "Received empty response from Gemini API"
    except Exception as e:
        return False, f"Cannot connect to Gemini API: {str(e)}"
