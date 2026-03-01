import os
import re
import time
from mistralai import Mistral, ToolFileChunk
from tools.utils import get_random_string

client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY"))

def generate_image(prompt, timestamp, config):
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