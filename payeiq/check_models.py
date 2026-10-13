import google.generativeai as genai
from decouple import config

# 1. Fetch the Gemini API key safely from your local .env file
GEMINI_API_KEY = config('GEMINI_API_KEY', default=None)

if not GEMINI_API_KEY:
    print("❌ Error: GEMINI_API_KEY is missing from your .env file!")
else:
    # 2. Pass the dynamic key to Google Generative AI
    genai.configure(api_key=GEMINI_API_KEY)

    try:
        print("--- Attempting to list models ---")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"Valid Model Name: {m.name}")
    except Exception as e:
        print(f"An error occurred: {e}")