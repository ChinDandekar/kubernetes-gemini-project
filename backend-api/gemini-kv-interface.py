import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

load_dotenv()
app = FastAPI()
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

isprod = os.environ["MODE"] == "prod"
local_kv_store = {}

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins; change this to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)


# Define request body schema
class QueryRequest(BaseModel):
    chatid: int
    query: str

@app.post("/answer_query/")
def answer_query(request: QueryRequest):
    if isprod:
        print("meow")
    else:
        context = local_kv_store.get(request.chatid, "")
    
    prompt = context + "**Query:** " + request.query + " \n**Answer:** "
    response = model.generate_content(prompt)
    
    if isprod:
        print("woof")
    else:
        local_kv_store[request.chatid] = prompt + response.text
        
    return {"chatid": request.chatid, 'reply': response.text}

@app.get("/load_chat/{chatid}")
def load_chat(chatid: int):
    return local_kv_store.get(chatid, "")

if __name__ == "__main__":
    import uvicorn
    port = 8000 if isprod else 8001
    uvicorn.run(app, host="0.0.0.0", port=port)

