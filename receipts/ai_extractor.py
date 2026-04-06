import google.generativeai as genai
import json
from PIL import Image
from django.conf import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")


def extract_receipt_data(file_path):
    try:
        img = Image.open(file_path)

        prompt = """
        You are reading a Nigerian PAYE tax receipt.

        Extract ONLY:
        - Date of Payment
        - Receipt Number
        - Amount Paid

        Return strictly in JSON format like this:
        {
          "date_of_payment": "YYYY-MM-DD",
          "receipt_number": "text",
          "amount": 12345,
          "confidence": "High" 
        }

        If unsure, reduce confidence to Medium or Low.
        """

        response = model.generate_content([prompt, img])
        text = response.text

        # Extract JSON from response
        start = text.find("{")
        end = text.rfind("}") + 1
        json_text = text[start:end]

        data = json.loads(json_text)
        return data

    except Exception as e:
        print("Gemini Error:", e)
        return {
            "date_of_payment": None,
            "receipt_number": None,
            "amount": None,
            "confidence": "Low"
        }