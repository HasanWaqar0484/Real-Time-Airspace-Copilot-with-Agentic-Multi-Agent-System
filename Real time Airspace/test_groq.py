import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

# Test if Groq API is working
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.1-8b-instant",
    temperature=0
)

try:
    response = llm.invoke("Say hello in one word")
    print(f"Success! Response: {response.content}")
except Exception as e:
    print(f"Error: {e}")
