import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
import os

load_dotenv()
app = FastAPI()
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

# Define request body schema
class QueryRequest(BaseModel):
    chatid: int
    query: str

@app.post("/answer_query/")
def answer_query(request: QueryRequest):
    prompt = "**Query:** " + request.query + " \n**Answer:** "
    response = model.generate_content(prompt)
    return {"chatid": request.chatid, 'ans': response.text}

@app.get("/load_chat/{chatid}")
def load_chat(chatid: int):
    return {"conversation": "Fake conversation"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

