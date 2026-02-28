from google import genai
from google.genai import types
import os
import dotenv

dotenv.load_dotenv()

# 1. Setup API Key from environment variable `genai_api_key`
client = genai.Client(api_key=os.getenv("genai_api_key"))

# 2. Configure the "System Instruction"
# This is like setting the "mode" for the AI before it even sees the data.
system_prompt = """
You are a data extraction bot for university students. 
Your goal is to look at Instagram captions and extract all important details from the caption as concisely as possible

Return the result as a single sentence condensing all the information into one brief line, and also above that on a separate indicate if there will be food (Food: [YES/NO] and what type / brand)
"""

def get_event_summary(caption):
    if not caption:
        return None

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=f"Follow the instructions and extract the information from the caption: {caption}",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
        ),
    )
    return response.text

