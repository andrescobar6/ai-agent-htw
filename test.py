from dotenv import load_dotenv
import google.generativeai as genai
import os

load_dotenv()  # Busca automáticamente un archivo .env
api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content("Explain how AI works in a few words")
print(response.text)