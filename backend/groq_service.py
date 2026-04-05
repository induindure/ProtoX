from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_ideas(domain, app_type):
    prompt = f"""
                Give me exactly 3 startup ideas in {domain} for a {app_type} app.

                Format strictly like this:

                Title: <title>
                Description: <description>
                - <feature>
                - <feature>
                - <feature>

                Repeat for all 3 ideas.
                """

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content