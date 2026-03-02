from google import genai
import os
import dotenv

dotenv.load_dotenv()

# 1. Setup API Key - replace before release
# rotate api_key="AIzaSyAZLHjsrkni5qRwG1bTckRVSNDHmnDx7s8" before release
client = genai.Client(api_key=dotenv.get_key("genai_api_key"))

# 2. Configure the "System Instruction"
# This is like setting the "mode" for the AI before it even sees the data.
system_prompt = """
You are a data extraction bot for university students. 
Your goal is to look at Instagram captions and extract all important details from the caption as concisely as possible

Return the result as a single sentence condensing all the information into one brief line, and also above that on a separate indicate if there will be food (Food: [YES/NO] and what type / brand)
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash-lite",
    system_instruction=system_prompt
)

def get_event_summary(caption):
    if not caption:
        return None
    
    response = model.generate_content(f"Analyze this caption: {caption}")
    return response.text

