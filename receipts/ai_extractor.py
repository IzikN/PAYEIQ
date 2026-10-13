import json
import os
import google.generativeai as genai
from decouple import config
from PIL import Image


def extract_receipt_data(file_path):
    # 1. Dynamically retrieve the API key at runtime
    api_key = config("GEMINI_API_KEY", default=os.getenv("GEMINI_API_KEY"))

    if not api_key:
        print("❌ Error: GEMINI_API_KEY is missing or empty.")
        return {
            "date_of_payment": None,
            "receipt_number": None,
            "amount": 0,
            "confidence": "Low",
        }

    genai.configure(api_key=api_key)

    try:
        # 2. Configure model with native structured JSON output
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",  # or "gemini-2.0-flash" / "gemini-2.5-flash"
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.1,  # Low temperature for precise extraction
            },
        )

        img = Image.open(file_path)

        prompt = """
        You are reading a Nigerian PAYE tax receipt.

        Extract ONLY:
        - Date of Payment (formatted as YYYY-MM-DD or null if missing)
        - Receipt Number (text string or null if missing)
        - Amount Paid (numeric integer or float value only, no currency symbols)
        - Confidence rating ("High", "Medium", or "Low")

        Required Schema:
        {
          "date_of_payment": "YYYY-MM-DD",
          "receipt_number": "text",
          "amount": 12345,
          "confidence": "High" 
        }
        """

        response = model.generate_content([prompt, img])

        # 3. Direct JSON parse (no string slicing needed)
        data = json.loads(response.text)
        return data

    except Exception as e:
        print("Gemini Error:", e)
        return {
            "date_of_payment": None,
            "receipt_number": None,
            "amount": 0,
            "confidence": "Low",
        }