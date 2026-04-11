from src.etl.prod.prompts.system_prompts import SYSTEM_PROMPTS
from datetime import datetime
from zoneinfo import ZoneInfo
from google import genai
import os
import dotenv

dotenv.load_dotenv()
    
def _get_system_prompt(name: str) -> str:
    """
    Resolve a system prompt by name from `prompts/system_prompts.py`.

    Teaching note:
    - This lets you quickly try different prompt variants without touching the summariser logic.
    - If you typo the name, we fall back to "concise_cot" instead of crashing mid-run.
    """
    prompt_template = (SYSTEM_PROMPTS.get(name) or SYSTEM_PROMPTS["concise_cot"]).strip()
    # If the template includes a placeholder, inject a fresh "now" string at call time.
    # This is how your `concise_cot` prompt gets the correct CURRENT_TIME value.
    if "{current_time_str}" in prompt_template:
        melb_tz = ZoneInfo("Australia/Melbourne")
        current_time_str = datetime.now(melb_tz).strftime("%A, %B %d, %Y at %I:%M %p")
        prompt_template = prompt_template.replace("{current_time_str}", current_time_str)
        return prompt_template
    raise ValueError(f"SYSTEM PROMPT NAME: {name} is not valid")



if __name__ == "__main__":
    prompt = _get_system_prompt("sugma")
    model = "gemini-2.5-flash-lite"
    model_input = {
        "club_id": "CISSA",
        "posts": [
            {
                "post_id": "1234567890",
                "timestamp": "2026-04-11T12:00:00Z",
                "caption": "CISSA is hosting an Industry Night on Tuesday at 6:00 PM featuring representatives from Google and Atlassian. Additionally, a free membership BBQ is scheduled for Friday at 1:00 PM on the Concrete Lawn. Both events require separate registrations via the provided links.",
            }
        ]
    }
    client = genai.Client(api_key=os.getenv("genai_api_key"))
    response = client.models.generate_content(
    # Import anything missing (json, types) at the top of your file for the below to work!
    # Also ensure 'system_prompt' is defined; here we use the fetched prompt or a fallback.

    model=model,  # selected model to use
    contents=__import__('json').dumps(model_input, ensure_ascii=False),  # serialize input as JSON; inline import for test
    config=genai.types.GenerateContentConfig(
        system_instruction=prompt,  # use system prompt variable defined above
        # teaching comment: forcing JSON output makes downstream parsing reliable
        response_mime_type="application/json",
    ),
    )
    print(response.text)