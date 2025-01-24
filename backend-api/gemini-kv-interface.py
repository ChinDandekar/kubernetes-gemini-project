import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import logging
from pydantic import BaseModel
import os
import json

load_dotenv()
app = FastAPI()
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")
llm_info = json.load(open(("llms.json")))
context_window = llm_info["google"]["gemini-1.5-flash"]["context_window"]

logger = logging.getLogger(__name__) # Get a logger instance
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
isprod = os.environ["MODE"] == "prod"

kvstore_service = os.environ.get("KVSTORE_SERVICE", "")
base_url = f"http://{kvstore_service}:9090"
local_kv_store = {"context_dict": {}}
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

@app.get("/get_context_window/{model_family}/{llm_name}")
def get_context_window(model_family: str, llm_name: str):
    context_window = llm_info[model_family][llm_name]['context_window']
    logger.info(f"context_window: {context_window}")
    return {"context_window": context_window}


@app.get("/get_all_models")
def get_all_models():
    return llm_info
# Define request body schema
class QueryRequest(BaseModel):
    chatid: int
    query: str

@app.post("/answer_query")
def answer_query(request: QueryRequest):
    user_query = request.query
    context = ""
    
    
    value = get_from_context_kv(request.chatid)
    if value and "context" in value:
        context = value["context"]
        messages = value["messages"]
    else:
        context = ""
        messages = []
    
    prompt = context + "**Query:** " + request.query + " \n**Answer:** "
    response = model.generate_content(prompt)
    tokens_used = response.usage_metadata.total_token_count
    
    
    messages.append({"length": len(user_query), "sender": "user", "text": user_query})
    messages.append({"length": len(response.text), "sender": "ai", "text": response.text})
    input_dict = {
        "context": prompt + response.text,
        "messages": messages,
        "tokens_used": tokens_used
    }
    
    logger.info(f"{tokens_used} tokens used for {context_window}")
    
    set_in_context_kv(request.chatid, input_dict)
            
        
    return {"chatid": request.chatid, 'reply': response.text, "tokens_used": tokens_used}

def set_in_context_kv(key, input_dict):
    if isprod:    
        get_context_url = base_url + f"/context/set/{key}"
        try:
            kv_set_response = requests.post(get_context_url, json=input_dict)
            kv_set_response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            response_json = kv_set_response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to KVStore: {e}")
        
    else:
        local_kv_store["context_dict"][key] = input_dict

def get_from_context_kv(key: int):
    if isprod:
        get_context_url = base_url + f"/context/get/{key}"
        try:
            kv_get_response = requests.get(get_context_url)
            kv_get_response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            value = kv_get_response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error("Error connecting to KVStore: %s", e, exc_info=True) # Log exceptions with traceback

    else:
        value = local_kv_store["context_dict"].get(key, None)
        logger.info("using local_kv_store")
        
    return value

@app.post("/test_post")
def test_post():
    return {"it": "works!"}

@app.get("/load_chat/{chatid}")
def load_chat(chatid: int):
    return get_from_context_kv(chatid)

@app.get("/load_all_chats")
def load_all_chats():
    return_dict = {}
    
    if isprod:
        get_keys_url = base_url + f"/context/all_keys"
        try:
            kv_get_response = requests.get(get_keys_url)
            kv_get_response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            keys = kv_get_response.json()['keys']
            
        except requests.exceptions.RequestException as e:
            logger.error("Error connecting to KVStore: %s", e, exc_info=True) # Log exceptions with traceback
            keys = []
    else:
        keys = list(local_kv_store["context_dict"].keys())
        
    
    for key in keys:
        value = get_from_context_kv(key)
        return_dict[key] = {"messages": value["messages"], "tokens_used": value["tokens_used"]}
    return [return_dict]

if __name__ == "__main__":
    import uvicorn
    port = 8000 if isprod else 8001
    uvicorn.run(app, host="0.0.0.0", port=port)

