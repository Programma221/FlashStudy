import requests
import time
from typing import List, Tuple, Optional
from decouple import config

HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
HUGGINGFACE_API_TOKEN = config("HF_API")
OR_API = config("OR_API")

headers = {
    "Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"
}

MAX_WORDS_PER_CHUNK = 700
MAX_CHARS_PER_CHUNK = 4530
MAX_CHUNKS = 3


def split_chunk_safely(text):
    words = text.split()
    mid = len(words) // 2
    return [' '.join(words[:mid]), ' '.join(words[mid:])]


def chunk_text(text):
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)
        chunk_str = ' '.join(current_chunk)
        if len(current_chunk) >= MAX_WORDS_PER_CHUNK or len(
                chunk_str) >= MAX_CHARS_PER_CHUNK:
            if len(current_chunk) > MAX_WORDS_PER_CHUNK or len(
                    chunk_str) > MAX_CHARS_PER_CHUNK:
                half1, half2 = split_chunk_safely(chunk_str)
                chunks.extend([half1, half2])
            else:
                chunks.append(chunk_str)
            current_chunk = []

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks[:MAX_CHUNKS]


def call_bart_api(text):
    response = requests.post(HUGGINGFACE_API_URL, headers=headers,
                             json={"inputs": text})
    if response.status_code == 200:
        return response.json()[0]['summary_text']
    return "Error: API call failed."


def summarize_text(text):
    chunks = chunk_text(text)
    summaries = []

    for i, chunk in enumerate(chunks[:MAX_CHUNKS]):
        summary = call_bart_api(chunk)
        summaries.append(summary)

    final_summary = "\n\n".join(summaries)

    return final_summary


def get_free_models() -> List[str]:
    """Fetch available free models from OpenRouter"""
    try:
        response = requests.get("https://openrouter.ai/api/v1/models",
                                timeout=10)
        response.raise_for_status()
        models_data = response.json()

        # Filter for free models (pricing.prompt = 0 and pricing.completion = 0)
        free_models = []
        for model in models_data.get('data', []):
            pricing = model.get('pricing', {})
            if (pricing.get('prompt') == '0' or pricing.get('prompt') == 0) and \
                    (pricing.get('completion') == '0' or pricing.get(
                        'completion') == 0):
                free_models.append(model['id'])

        return free_models

    except Exception as e:
        # Fallback to some known free models
        return [
            "meta-llama/llama-3.2-1b-instruct:free",
            "meta-llama/llama-3.2-3b-instruct:free",
            "microsoft/phi-3-mini-128k-instruct:free",
            "google/gemma-2-9b-it:free",
            "qwen/qwen-2-7b-instruct:free"
        ]


def create_cards(text: str, number: int, models: List[str],
                 existing_questions: List[str]) -> Optional[
    List[Tuple[str, str]]]:
    """Try to create cards using available models, avoiding duplicate questions"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": "Bearer " + OR_API,
        "Content-Type": "application/json"
    }

    # Build the existing questions context
    existing_context = ""
    if existing_questions:
        existing_context = f"\n\nIMPORTANT: Do NOT create questions similar to these already created questions: {'; '.join(existing_questions)}. Make sure your questions cover DIFFERENT aspects of the text."

    prompt = f"""Create {number} question answer pairs based on the text at the bottom. 
Format them EXACTLY in this way: 
|Question? $$ Answer|
|Question? $$ Answer|
|Question? $$ Answer|

Format explanation: Encase the qna pairs in pipes and separate the question 
from the answer with two dollar signs. There should be {number * 2} | and 
{number * 2} $.{existing_context}

This is the text to base the questions on: {text}"""

    for model in models:
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000,
            "temperature": 0.8
        }

        try:
            response = requests.post(url, headers=headers, json=data,
                                     timeout=45)
            response.raise_for_status()
            response_json = response.json()

            # Check for API errors
            if "error" in response_json:
                continue

            if "choices" not in response_json or not response_json["choices"]:
                continue

            content = response_json["choices"][0]["message"]["content"]

            # Parse the content
            if "|" not in content or "$$" not in content:
                continue

            qnaextra = content.split("|")
            qna = [item for item in qnaextra if "$$" in item]

            if len(qna) < number:
                continue

            # Parse question-answer pairs
            parsed_qna = []
            for item in qna:
                if "$$" in item:
                    parts = item.split("$$", 1)
                    if len(parts) == 2:
                        question = parts[0].strip()
                        answer = parts[1].strip()
                        if question and answer:
                            parsed_qna.append((question, answer))

            if len(parsed_qna) >= number:
                return parsed_qna[:number]

        except:
            continue

        time.sleep(1)

    return None


def generate_flashcards(text: str, number: int) -> Optional[
    List[Tuple[str, str]]]:
    """Generate flashcards with automatic model switching and duplicate prevention"""
    if not (0 < number < 7):
        return None

    # Get available free models
    available_models = get_free_models()
    if not available_models:
        return None

    cards = []
    existing_questions = []
    remaining = number
    max_attempts = 3

    for attempt in range(max_attempts):
        while remaining > 0:
            # Use original chunking logic
            num_to_generate = remaining // 2 if remaining > 3 else remaining

            new_cards = create_cards(text, num_to_generate, available_models,
                                     existing_questions)

            if new_cards:
                # Add new questions to tracking list
                for question, answer in new_cards:
                    existing_questions.append(question)

                cards.extend(new_cards)
                remaining -= len(new_cards)
            else:
                break

        if remaining == 0:
            return cards
        else:
            available_models = get_free_models()
            time.sleep(2)

    return cards if cards else None
