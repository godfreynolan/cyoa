from flask import Flask, request, render_template
from openai import OpenAI
import config
import re
from typing import Mapping

client = OpenAI(api_key=config.OPENAI_API_KEY)

app = Flask(__name__)

system_directive = """
You, 'assistant', are telling me, 'user', an interactive choose-your-own-adventure story. Your repsonses are with labels so I can parse them and display them in a user interface.
Each step of the story, you present the following information.
Story. The current state of the story.
Caption. A detailed caption showing the current state of the story to be used as a DALL-E image prompt. It should be as consistent as possible with the previous caption.
Choice1. The text of the first choice.
Choice2. The text of the second choice.
Your image captions should be concise but repeat specific details about the setting, characters, and objects in the story to help generate consistent images across repeated invocations.
Present exactly two choices to the user. Never offer blank (empty) choices.
Only present choices that build on the story. Do not present choices that lead the main character away from action or conflict (such as "going home").
Do not repeat yourself.
An example exchange is as follows:

user:
A wizard enters a dungeon.

assistant:
Story: An aged wizard quietly enters a dark dungeon. He can tell by the echo of his footsteps that the chamber is large and seemingly empty.
Caption: A grey-bearded wizard with a flowing blue cloak, a blue hat, a long grey beard, and a 6-foot wooden staff entering a dark dungeon with high-ceilings from the left side of the frame.
Choice1: The wizard illuminates the dungeon
Choice2: The wizard turns himself invisble

user:
The wizard illuminates the dungeon

assistant:
Story: The wizard illuminates the tip of his staff and lights the room. In the light, he sees a giant ogre! The ogre leaps at him.
Caption: On the left, a grey-bearded wizard with a flowing blue cloak, a blue hat, a long grey beard illuminates a high-ceilinged dark dungeon with the 6-foot wooden staff he carries. An 8-foot hulking ogre wearing a tattered brown tunic and an axe lunges at the wizard from the right side of the frame.
Choice1: The wizard steps aside, dodging the ogre.
Choice2: The wizard casts a spell, freezing the ogre in place.

user:
The wizard casts a spell, freezing the ogre in place.

assistant:
Story: The wizard casts "petrificus schmetrificus", freezing the ogre in mid-air.
Caption: In a high-ceilinged dark dungeon, a wizard with a flowing blue cloak, a blue hat, a long grey beard, and a 6-foot wooden staff stands to the left. He has petrified an 8-foot hulking ogre that wears a tattered brown tunic and holds an axe that was lunging towards him from the right side of the frame.
Choice1: The wizard looks through the ogres pockets.
Choice2: The wizard, fearing his spell will wear off, hurries away.
""".strip()


def generate_image(image_caption, dimensions=(1792, 1024)):
    image_response = client.images.generate(
        model="dall-e-3",
        prompt=(image_caption[:1000]),
        n=1,
        size=f"{dimensions[0]}x{dimensions[1]}"
    )
    return image_response.data[0].url

def generate_cyoa(choice):
    messages_payload = [{"role": "system", "content": system_directive}, {"role": "user", "content": choice}]

    chat_response = client.chat.completions.create(
            model="gpt-4o",  
            messages=messages_payload, 
            frequency_penalty=1.0, temperature=0.8
    )
        
    return chat_response.choices[0].message

@app.route('/')
def index():
    img_path=generate_image("generate a picture that illustrates the concept of a choose your own adventure game")
    story="Click on a button below to start your adventure!"
    button_name1 = "A knight discovers a hidden enchanted castle"
    button_name2 = "A scientist uncovers a portal to an alien world"
    return render_template('index.html', story=story, button_name1=button_name1, button_name2=button_name2, img_path=img_path)

def get_caption(chat_response_object: Mapping) -> str:
    return (
        re.search(r"Caption:(.*)(?:\n|$)", chat_response_object.content)
        .group(1)
        .strip()
    )

def get_story(chat_response_object: Mapping) -> str:
    return (
        re.search(r"Story:(.*)(?:\n|$)", chat_response_object.content)
        .group(1)
        .strip()
    )

def get_choice1(chat_response_object: Mapping) -> str:
    return (
        re.search(r"Choice1:(.*)(?:\n|$)", chat_response_object.content)
        .group(1)
        .strip()
    )

def get_choice2(chat_response_object: Mapping) -> str:
    return (
        re.search(r"Choice2:(.*)(?:\n|$)", chat_response_object.content)
        .group(1)
        .strip()
    )

@app.route('/submit', methods=['POST'])
def submit():
    choice = request.form['choice']
    cyoa = generate_cyoa(choice)
    caption_text = get_caption(cyoa)
    story_text = get_story(cyoa)
    choice1_text = get_choice1(cyoa)
    choice2_text = get_choice2(cyoa)
    img_path = generate_image(caption_text)
    return render_template('index.html', story=story_text, button_name1=choice1_text, button_name2=choice2_text, img_path=img_path)


if __name__ == '__main__':
    app.run(debug=True)
