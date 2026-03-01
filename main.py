import os
import sys
import csv
import time
import re
from datetime import datetime
from tools.config_handler import get_config
from tools.sentence_processing import get_translation, generate_example_sentence
from tools.image_generation import generate_image
from tools.audio_generation import generate_audio
from tools.utils import clean_html

CONFIG_FILE = "sentenceMining.config"

def process_source_file(config):
    os.makedirs(config["output_folder"], exist_ok=True)
    if not os.path.isdir(config["media_folder"]):
        print(f"Media folder does not exist: {config['media_folder']}")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    csv_filename = f"DanishSentences-{timestamp}.csv"
    csv_filepath = os.path.join(config["output_folder"], csv_filename)

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
        if regex.search(line):
            sentence = line.replace('**', '<b>', 1).replace('**', '</b>', 1)
            word = re.search(r'\*\*(.*?)\*\*', line).group(1)
        else:
            word = line
            sentence = generate_example_sentence(word)

        n += 1
        print(f"[{n}/{total_lines}] processing word <{word}>")

        translation = get_translation(sentence)
        clean_sentence = clean_html(sentence)
        clean_translation = clean_html(translation)

        image_filename = '<img src=\'' + generate_image(clean_sentence, timestamp, config) + '\'>'
        audio_filename = '[sound:' + generate_audio(clean_sentence, timestamp, config) + ']'

        csv_data.append({
            'Sentence': sentence,
            'Word': word,
            'Image': image_filename,
            'Meaning': translation,
            'Audio': audio_filename
        })
        time.sleep(1)

    with open(csv_filepath, 'w', encoding='utf-8', newline='') as csvfile:
        fieldnames = ['Sentence', 'Word', 'Image', 'Meaning', 'Audio']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(csv_data)

    print(f"Processing complete. CSV file saved at: {csv_filepath}")

if __name__ == "__main__":
    config_filename = CONFIG_FILE
    if len(sys.argv) > 2:
        print("Usage: python script.py [config filename]")
        sys.exit(1)
    elif len(sys.argv) == 2:
        config_filename = sys.argv[1]

    config = get_config(config_filename)
    if not os.path.isfile(config["source_file"]):
        print(f"Error: Source file {config['source_file']} does not exist.")
        sys.exit(1)

    process_source_file(config)
