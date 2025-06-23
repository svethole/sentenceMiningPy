# sentenceMiningPy
This is a lazy and pretty bare-bones script to assist sentence mining (see AJATT) in conjunction with Anki.

## Setup

### programs

Stuff you need to install
* Python v3
* pip
* git

### preparing the python environment
* create a virtual environment in the project root folder ```python3 -m venv openai-env```
* source the activate file from the newly created folder structure ```source openai-env/bin/activate```
* install any required dependencies e.g. ```pip install openai deep_translator gtts configparser deepl```
* note: the given list is very likely incomplete for your system, just run the script and install whatever is necessary

### getting your API keys
The script makes use of OpenAI to generate images and DeepL for translation. Unfortunately, the OpenAI key is not free but inexpensive.
* create an account at https://openai.com/api/
* visit the Dashboard
* open the file called ```environment``` in the root folder of the script
* insert the key on the right side of the equal sign for ```OPEN_AI_KEY``` (no quotes needed)
* rename the ```environment``` file you just edited to ```.env```, this will hide the file; it will be read automatically and its values imported into the script

Next, you need your DeepL API key. This one's for free for up 500.000 characters per month, which has always been enough for me so far.
* create an account at http://deepl.com
* go to your account page and from there to API keys & limits
* create your key, copy it and insert it in the script file as value for ```deepl_auth_key```
* open the ```.env``` from above and insert your ```DEEPL_KEY``` likewise

### adjusting the config
There are two pre-made config files that need to be renamed ```sentenceMining.config```. 
Adjust the values according to your needs:
* ```target_language```: See this page for valid language codes: https://developers.deepl.com/docs/getting-started/supported-languages
* ```source_language```: same
* ```sentence_file```: full path to the file containing your collected sentences
* ```output_folder```: full path to where you want the CSV file to be saved - this is the file you will need to import to Anki
* ```media_folder```: full path to the folder where Anki keeps your image and sound files. For macOS this is usually ```/Users/<USERNAME>/Library/Application Support/Anki2/<COLLECTION NAME>/collection.media```
* ```debug```: boolean
* ```debug_sentence_file```: if you want to make use of a separate sentence file for debug purposes
* ```debug_output_folder```: same as ```output_folder``` but for debug runs
* ```debug_media_folder```: same as ```media_folder``` but for debug runs

## the sentence file
The script expects two formats of sentences or words.
A sentence with one or more highlighted words. Highlight the word or words by enclosing them in double asterisks:
* ```In de tuin bevinden zich bovendien een **glijbaan** en een schommel.```
* ```Risken för biverkningar är liten. Efteråt har du en kateter i urinröret **under några veckor**.```

Or you can just have one or more unenclosed words on a line, which has the script come up with a sentence around the given expression and then proceed as if you had provided it with the such generated sentence in the first place. Take this example:
```elétrico```
The script might then come up with the following sentence: Choques *elétricos* podem ocorrer mesmo com baixa exposição à alta tensão.

## preparing Anki
You need a specific Note format in order to make it work with the generated CSV.
* to create a new note type, go to Tools -> Manage Note Types
* click ```Add```
* Add the following fields
  - Sentence
  - Word (tick ```Sort by this field in the browser```)
  - Image
  - Meaning
  - Audio
  - Notes (tick ```Use HTML editor by default```)
 
* Select the newly created Note Type
* click ```Cards```
  - edit the ```Front Template``` so that it contains this single line
    ```
    {{Sentence}}
    ```
  - edit the ```Back Template``` and insert the following code:
    ```html
    {{FrontSide}}

    <hr id=answer>
    <div class="card_image">{{Image}}</div>
    <br />
    <div class="meaning">{{Meaning}}</div>
    <br />
    <div class="notes">{{Notes}}</div>

    {{Audio}}
    ```
  - insert the following CSS under ```Styling```
    ```css
    .card {
      font-family: arial;
      font-size: 20px;
      text-align: center;
      color: #4b70b4;
      background-color: white;
    }
    
    .sentence {
    }
    
    .meaning {
    	font-size: 16px;
    	color: #92a8d1;
    }
    
    .notes {
    	font-size: 14px;
    	color: #92a8d1;
    	font-style: italic;
    }

    .card_image {
    	margin-left: auto;
    	margin-right: auto;
    	max-width: 300px;
    }
    ```

## importing the CSV in Anki
In Anki's main window, click ```Import File``` at the bottom right. Navigate to the output folder you specified under ```output_folder``` in your config file earlier and load the CSV. In the next dialogue, make sure that the fields from the CSV line up with the fields in your Anki cards, i.e. ```Sentence``` -> ```Sentence```, ```Image``` -> ```Image``` and so on. Then select a deck you want to import the newly generated cards into and confirm.
It is generally a good idea to go over all of the generated cards by previewing them as the next step as translations sometimes can be a bit off and you might want to add your own notes or images.

## other things
* Currently, the instructions for the image generation are still hard coded in the function ```def generate_image(sentence, output_folder, timestamp)``` You might want to adjust the prompt to your needs if you are not learning Danish.
* As noted above, DeepL is an astonishingly good translator in most cases. That does not mean, however, that it doesn't make some blatant errors from time to time. You might want to quickly check if the translations make sense once you've imported newly generated cards.
* For some reason - mostly timeouts or content violation policies - OpenAI sometimes refuses to generate an image. In this case you can have an image generated manually by using Bing for example or just searching the net for something fitting.
