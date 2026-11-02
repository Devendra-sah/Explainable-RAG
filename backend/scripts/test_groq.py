
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)

api_key = os.getenv("GROQ_API_KEY")
model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

if not api_key:
    raise ValueError("GROQ_API_KEY is missing from backend/.env")

client = Groq(api_key=api_key)

response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "system",
            "content": "You are an assistant for an explainable RAG database project."
        },
        {
            "role": "user",
            "content": "Explain database normalization in two simple sentences."
        }
    ],
    reasoning_effort="low"
)

print("Model:", model)
print("Response:")
print(response.choices[0].message.content)
