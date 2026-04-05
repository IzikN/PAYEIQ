import google.generativeai as genai

# PUT YOUR REAL KEY HERE
genai.configure(api_key="AIzaSyBWZ1Lag1_XVH78KtDbf86WUTSlwTAKQ_I")

try:
    print("--- Attempting to list models ---")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Valid Model Name: {m.name}")
except Exception as e:
    print(f"An error occurred: {e}")