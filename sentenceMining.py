import os
import csv
import re
import sys
import time
import configparser
import deepl
import random, string
from datetime import datetime
from openai import OpenAI
# from deep_translator import GoogleTranslator
from gtts import gTTS

client = 

deepl_auth_key = 
translator = deepl.Translator(deepl_auth_key)

# to setup run
#   python3 -m venv openai-env
#   source openai-env/bin/activate
#   pip install openai deep_translator gtts configparser deepl

# OpenAI API key configuration

# Translate helper
# translator = GoogleTranslator(source='da', target='en')

debug = False

CONFIG_FILE = "sentenceMining.config"

# regex to strip XML tags
CLEANR = re.compile('<.*?>') 

# we're going to remove XML tags on the fly in sentences before
# outputting them to the CSV
def clean_html(raw_html):
  cleantext = re.sub(CLEANR, '', raw_html)
  return cleantext

def get_random_string(n):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

def get_translation(sentence):    
    try:
        return translator.translate_text(sentence, source_lang="da", target_lang="en-gb").text
    except Exception as e:
        print(f"Failed translating sentence: <{sentence}>")
        print(f"Message: {e}")
        return "<NO TRANSLATION AVAILABLE>"

def generate_image(sentence, output_folder, timestamp):
    if debug:
        return 'debug_dummy_image_filename.png'
    
    try:
        # Generate image prompt
        response = client.images.generate(prompt=f"Et realistisk fotografi, der afbilder: '{sentence}'. Fotografiet skulle vise en begivenhed som finder sted i Danmark.",
        model="dall-e-3",
        n=1)
        image_url = response.data[0].url

        # Save the image file
        random_string = get_random_string(5)
        image_filename = f"{'_'.join(sentence.split()[:3])}-{timestamp}-{random_string}.png"
        image_filename = re.sub('[^A-Za-z0-9.]+', '', image_filename)
        image_filepath = os.path.join(output_folder, image_filename)
        # Download and save the image from the URL
        import requests
        image_data = requests.get(image_url).content
        with open(image_filepath, 'wb') as file:
            file.write(image_data)

        return image_filename
    except Exception as e:
        print(f"Error generating image: {e}")
        return ""

def generate_audio(sentence, output_folder, timestamp):
    if debug:
        return 'debug_dummy_audio_filename.mp3'
    
    try:
        audio = gTTS(text=sentence, lang='da', slow=False)
        
        # save the file
        random_string = get_random_string(5)
        audio_filename = f"{'_'.join(sentence.split()[:3])}-{timestamp}-{random_string}.mp3"
        audio_filename = re.sub('[^A-Za-z0-9.]+', '', audio_filename)
        audio_filepath = os.path.join(output_folder, audio_filename)
        
        audio.save(audio_filepath)
        
        return audio_filename
    except Exception as e:
        print(f"Error generating audio: {e}")
        return ""

def generate_example_sentence(word):
    fallback_return = f"{word} er meget almindeligt i Danmark."
    #if debug:
    #    return fallback_return
    
    try:
        response = client.chat.completions.create(model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an assistant skilled in creating natural Danish sentences."},
            {"role": "user", "content": f"Generate a natural Danish sentence using the expression '{word}'."}
        ],
        max_tokens=50)
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating example sentence: {e}")
        return fallback_return

def process_source_file(input_file, output_folder, media_folder):
    # Create output folder structure
    os.makedirs(output_folder, exist_ok=True)

    # do not try to create media folder
    if not os.path.isdir(media_folder):
        print(f"Media folder does not exist: {media_folder}")
        sys.exit(1)

    # Generate CSV filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    csv_filename = f"DanishSentences-{timestamp}.csv"
    csv_filepath = os.path.join(output_folder, csv_filename)

    # Process input file
    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    csv_data = []

    n = 0
    total_lines = len(lines)
    for line in lines:
        line = line.strip()
        if not line:
            continue

        if '**' in line:  # Sentence with focus word
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
        image_filename = '<img src=\'' + generate_image(clean_translation, media_folder, timestamp) + '\'>'
        
        # Generate audio
        audio_filename = '[sound:' + generate_audio(clean_sentence, media_folder, timestamp) + ']'

        # Add to CSV data
        csv_data.append({
            'Sentence': sentence,
            'Word': word,
            'Image': image_filename,
            'Meaning': translation,
            'Audio': audio_filename
        })
        
        # we don't want to run into rate limits, they're usually 5 images per 1 minute for OpenAI, so sleeping for ten seconds should do the trick
        time.sleep(10)

    # Write CSV file
    with open(csv_filepath, 'w', encoding='utf-8', newline='') as csvfile:
        fieldnames = ['Sentence', 'Word', 'Image', 'Meaning', 'Audio']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(csv_data)

    print(f"Processing complete. CSV file saved at: {csv_filepath}")

if __name__ == "__main__":
    config_file = CONFIG_FILE

    # check command line args
    if len(sys.argv) > 2:
        print("Usage: python script.py [config file]")
        sys.exit(1)
    elif len(sys.argv) == 2:
        config_file = sys.argv[1]

    # read config
    if not os.path.isfile(config_file):
        print(f"Error: Config file '{config_file}' does not exist.")
        sys.exit(1)
    
    config = configparser.ConfigParser()
    config.read(config_file)
    
    source_file   = config['global']['sentence_file']
    output_folder = config['global']['output_folder']
    media_folder  = config['global']['media_folder']
    
    debug = config['debug'].getboolean('debug')
    if debug:
        if config['debug']['debug_sentence_file']:
            source_file = config['debug']['debug_sentence_file']
            
        if config['debug']['debug_output_folder']:
            output_folder = config['debug']['debug_output_folder']
            
        if config['debug']['debug_media_folder']:
            media_folder = config['debug']['debug_media_folder']

    if not os.path.isfile(source_file):
        print(f"Error: Source file '{source_file}' does not exist.")
        sys.exit(1)

    process_source_file(source_file, output_folder, media_folder)
