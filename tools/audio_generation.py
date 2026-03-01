import os
import re
import time
from gtts import gTTS
from mistralai import Mistral, ToolFileChunk
from tools.utils import get_random_string

def generate_audio(sentence, timestamp, config):
    if os.getenv("DEBUG"):
        return 'debug_dummy_audio_filename.mp3'

    try:
        audio = gTTS(text=sentence, lang='da', slow=False)
        random_string = get_random_string(5)
        audio_filename = f"{'_'.join(sentence.split()[:3])}-{timestamp}-{random_string}.mp3"
        audio_filename = re.sub('[^A-Za-z0-9.]+', '', audio_filename)
        audio_filepath = os.path.join(config["media_folder"], audio_filename)

        audio.save(audio_filepath)
        return audio_filename
    except Exception as e:
        print(f"Error generating audio: {e}")
        return ""