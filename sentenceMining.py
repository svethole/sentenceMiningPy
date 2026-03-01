import os
import csv
import re
import sys
import time
import configparser
import deepl
import random, string
from datetime import datetime
from gtts import gTTS
from dotenv import load_dotenv
from mistralai import Mistral, UserMessage, SystemMessage
from mistralai.models import ToolFileChunk

CONFIG_FILE = "sentenceMining.config"

# get secrets
load_dotenv()
mistral_model = "mistral-medium-2505"
client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY"))
translator = deepl.Translator(os.getenv("DEEPL_KEY"))

DEBUG = os.getenv("DEBUG")

# regex to strip XML tags
CLEANR = re.compile('<.*?>')

config = {}

def get_config(config_filename):
    if not os.path.isfile(config_filename):
        print(f"Error: Config file '{config_filename}' does not exist.")
        sys.exit(1)
        
    config_data = configparser.ConfigParser()
    config_data.read(config_filename)
    
    if DEBUG:
        config["source_file"]   = config_data['debug']['debug_sentence_file']
        config["output_folder"] = config_data['debug']['debug_output_folder']
        config["media_folder"]  = config_data['debug']['debug_media_folder']
    else:
        config["source_file"]   = config_data['global']['sentence_file']
        config["output_folder"] = config_data['global']['output_folder']
        config["media_folder"]  = config_data['global']['media_folder']

# we're going to remove XML tags on the fly in sentences before
# outputting them to the CSV
def clean_html(raw_html):
  cleantext = re.sub(CLEANR, '', raw_html)
  return cleantext

def get_random_string(n):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

def get_translation(sentence):    
    try:
        return translator.translate_text(sentence, source_lang="da", target_lang="de").text
    except Exception as e:
        print(f"Failed translating sentence: <{sentence}>")
        print(f"Message: {e}")
        return "<NO TRANSLATION AVAILABLE>"

def generate_image(prompt, timestamp):
    try:
        image_agent = client.beta.agents.create(
            model="mistral-medium-latest",
            name="Sentence Mining Image Generation Agent",
            description="Agent to be used with SentenceMining.py",
            instructions="Create a realistic image, set in Denmark, no text in image",
            tools=[{"type": "image_generation"}],
            completion_args={
                "temperature": 0.3,
                "top_p": 0.95,
            }
        )
        response = client.beta.conversations.start(
            agent_id=image_agent.id,
            inputs=f"Generate an image adhering to the following instructions: {prompt}",
            stream=False
        )

        image_paths = []
        if hasattr(response, 'outputs'):
            for output in response.outputs:
                if hasattr(output, 'content'):
                    if isinstance(output.content, list):
                        for i, chunk in enumerate(output.content):
                            if isinstance(chunk, ToolFileChunk):
                                try:
                                    # Save the image file
                                    random_string = get_random_string(5)
                                    image_filename = f"{'_'.join(prompt.split()[:3])}-{timestamp}-{random_string}.png"
                                    image_filename = re.sub('[^A-Za-z0-9.]+', '', image_filename)
                                    image_filepath = os.path.join(config["media_folder"], image_filename)

                                    file_bytes = client.files.download(file_id=chunk.file_id).read()
                                    with open(image_filepath, "wb") as file:
                                        file.write(file_bytes)
                                    image_paths.append(image_filename)
                                except Exception as e:
                                    print(f"Error processing image chunk: {str(e)}")
                    else:
                        print(f"Content is not a list: {output.content}")
        if image_paths:
            return image_paths[0]
        else:
            print("No images were generated")
            return ""
    except Exception as e:
        print(f"Error during image generation: {str(e)}")
        if hasattr(e, '__dict__'):
            print(f"Error details: {e.__dict__}")
        return ""

def generate_audio(sentence, timestamp):
    if DEBUG:
        return 'debug_dummy_audio_filename.mp3'
    
    try:
        audio = gTTS(text=sentence, lang='da', slow=False)
        
        # save the file
        random_string = get_random_string(5)
        audio_filename = f"{'_'.join(sentence.split()[:3])}-{timestamp}-{random_string}.mp3"
        audio_filename = re.sub('[^A-Za-z0-9.]+', '', audio_filename)
        audio_filepath = os.path.join(config["media_folder"], audio_filename)
        
        audio.save(audio_filepath)
        
        return audio_filename
    except Exception as e:
        print(f"Error generating audio: {e}")
        return ""

def generate_example_sentence(word):
    fallback_return = f"{word} er meget almindeligt i Danmark."
    #if DEBUG:
    #    return fallback_return
    
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

def process_source_file():
    # Create output folder structure
    os.makedirs(config["output_folder"], exist_ok=True)

    # do not try to create media folder
    if not os.path.isdir(config["media_folder"]):
        print(f"Media folder does not exist: {config['media_folder']}")
        sys.exit(1)

    # Generate CSV filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    csv_filename = f"DanishSentences-{timestamp}.csv"
    csv_filepath = os.path.join(config["output_folder"], csv_filename)

    # Process input file
    with open(config["source_file"], 'r', encoding='utf-8') as file:
        lines = file.readlines()

    csv_data = []

    n = 0
    total_lines = len(lines)
    for line in lines:
        line = line.strip()
        if not line:
            continue

        regex = re.compile(r'\*\*(.*?)\*\*')
        if regex.search(line):  # Sentence with focus word
            sentence = line.replace('**', '<b>', 1).replace('**', '</b>', 1)
            word = re.search(r'\*\*(.*?)\*\*', line).group(1)
        else:  # Single word
            word = line
            sentence = generate_example_sentence(word)

        n += 1
        print(f"[{n}/{total_lines}] processing word <{word}>")

        # Translate sentence
        translation = get_translation(sentence)

        clean_sentence    = clean_html(sentence)
        clean_translation = clean_html(translation)
        
        # Generate image
        image_filename = '<img src=\'' + generate_image(clean_sentence, timestamp) + '\'>'
        
        # Generate audio
        audio_filename = '[sound:' + generate_audio(clean_sentence, timestamp) + ']'

        # Add to CSV data
        csv_data.append({
            'Sentence': sentence,
            'Word': word,
            'Image': image_filename,
            'Meaning': translation,
            'Audio': audio_filename
        })
        
        # we don't want to run into rate limits, they're usually 5 images per 1 minute for OpenAI, so sleeping for ten seconds should do the trick
        time.sleep(1)

    # Write CSV file
    with open(csv_filepath, 'w', encoding='utf-8', newline='') as csvfile:
        fieldnames = ['Sentence', 'Word', 'Image', 'Meaning', 'Audio']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(csv_data)

    print(f"Processing complete. CSV file saved at: {csv_filepath}")

if __name__ == "__main__":

    config_filename = CONFIG_FILE
    
    # check command line args
    if len(sys.argv) > 2:
        print("Usage: python script.py [config filename]")
        sys.exit(1)
    elif len(sys.argv) == 2:
        config_filename = sys.argv[1]

    # read config
    get_config(config_filename)

    if not os.path.isfile(config["source_file"]):
        print(f"Error: Source file {config['source_file']} does not exist.")
        sys.exit(1)

    process_source_file()
