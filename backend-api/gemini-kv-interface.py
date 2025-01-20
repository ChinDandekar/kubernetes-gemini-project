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
# the 'schema' of this store will be:
# {
    # chatid: 
    # { 
        # messages:
        # [
            # {length: 5, sender: "user", text: "meow"}  // msg1
        # ]
        # context: "**Query**: meow \n**Answer**: meow!"
# }

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
    user_query = request.query
    context = ""
    
    if isprod:
        print("meow")
    else:
        context = local_kv_store.get(request.chatid, {"context": ""})["context"]

    
    prompt = context + "**Query:** " + request.query + " \n**Answer:** "
    response = model.generate_content(prompt)
    
    if isprod:
        print("woof")
    else:
        if request.chatid not in local_kv_store:
            local_kv_store[request.chatid] = {"context": "", "messages": []}
            
        local_kv_store[request.chatid]["context"] = prompt + response.text
        local_kv_store[request.chatid]["messages"].append({"length": len(user_query), "sender": "user", "text": user_query})
        local_kv_store[request.chatid]["messages"].append({"length": len(response.text), "sender": "ai", "text": response.text})
        
        
    return {"chatid": request.chatid, 'reply': response.text}

@app.get("/load_chat/{chatid}")
def load_chat(chatid: int):
    return local_kv_store.get(chatid, "")

@app.get("/load_all_chats")
def load_all_chats():
    return_dict = {}
    for chatid in local_kv_store:
        return_dict[chatid] = local_kv_store[chatid]["messages"]
    return [return_dict]

if __name__ == "__main__":
    import uvicorn
    port = 8000 if isprod else 8001
    uvicorn.run(app, host="0.0.0.0", port=port)

