from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model= "gemini-3.5-flash",
    temperature=0.2,
)

def ask_llm(prompt: str) -> str:
    response = llm.invoke(prompt)
    if isinstance(response.content, str):
        return response.content

    return "".join(
        block["text"]
        for block in response.content
        if block.get("type") == "text"
    )