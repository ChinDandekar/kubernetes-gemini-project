import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI
import os

load_dotenv()
app = FastAPI()
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")


@app.get("/answer_query/{chatid}")
def answer_query(chatid: int, query: str):
    prompt = "**Query:** " + query + " \n**Answer:** "
    response = model.generate_content(prompt)
    return {"chatid": chatid, 'ans': response.text}

@app.post("/answer_query/{chatid}")
def answer_query(chatid: int, query: str):
    prompt = "**Query:** " + query + " \n**Answer:** "
    response = model.generate_content(prompt)
    return {"chatid": chatid, 'ans': response.text}

@app.get("/load_chat/{chatid}")
def load_chat(chatid: int):
    return {"conversation": "Fake conversation"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

