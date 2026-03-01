import deepl
import os
from mistralai import Mistral
from tools.utils import clean_html

translator = deepl.Translator(os.getenv("DEEPL_KEY"))
client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY"))

def get_translation(sentence):
    try:
        return translator.translate_text(sentence, source_lang="da", target_lang="de").text
    except Exception as e:
        print(f"Failed translating sentence: <{sentence}>")
        print(f"Message: {e}")
        return "<NO TRANSLATION AVAILABLE>"

def generate_example_sentence(word):
    fallback_return = f"{word} er meget almindeligt i Danmark."
    try:
        chat_response = client.chat.complete(
            model="mistral-medium-latest",
            messages=[
                {
                    "role": "user",
                    "content": f"Generate a single Danish sentence using the expression '{word}', that I can use as is for a language-learning flashcard. I only want a single Danish sentence, nothing else."
                },
            ],
            safe_prompt=True,
        )
        return chat_response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating example sentence: {e}")
        return fallback_return
