import os
import sys
import configparser
from dotenv import load_dotenv

load_dotenv()
DEBUG = os.getenv("DEBUG")

def get_config(config_filename):
    if not os.path.isfile(config_filename):
        print(f"Error: Config file '{config_filename}' does not exist.")
        sys.exit(1)

    config_data = configparser.ConfigParser()
    config_data.read(config_filename)

    config = {}
    if DEBUG:
        config["source_file"]   = config_data['debug']['debug_sentence_file']
        config["output_folder"] = config_data['debug']['debug_output_folder']
        config["media_folder"]  = config_data['debug']['debug_media_folder']
    else:
        config["source_file"]   = config_data['global']['sentence_file']
        config["output_folder"] = config_data['global']['output_folder']
        config["media_folder"]  = config_data['global']['media_folder']

    return config
