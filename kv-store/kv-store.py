import requests
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import kubernetes.client
from kubernetes import config
from dotenv import load_dotenv
load_dotenv()
namespace = os.environ.get("NAMESPACE", "default")  


global peer_count
global instance_id
instance_id = int(os.environ.get("HOSTNAME", "kvstore-0").split("-")[1])

# Using lifespan to handle startup and shutdown
async def lifespan(app: FastAPI):
    # Startup logic
    global instance_id
    global peer_count
    print("Application startup")
    peer_count = get_peers_count()
    print(f"Number of peers: {peer_count}")
    
    
    for i in range(peer_count):
        if i == instance_id:  # Skip self
            continue
        peer_url = get_peer_url(i)
        try:
            response = requests.get(f'{peer_url}/check')
            print(f"Response from {peer_url}: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to connect to {peer_url}: {e}")

    yield  # This ensures the lifespan function doesn't block and the app starts up.

    # Shutdown logic can be placed here
    print("Application shutdown")


app = FastAPI(lifespan=lifespan)
# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins; change this to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# Dummy in-memory store for demonstration
kv_store = {"context_dict": {}}

def get_peer_url(index):
    # The DNS name for each peer will follow the format <pod-name>.<service-name>
    return f'http://kvstore-{index}.kvstore-internal.{namespace}.svc.cluster.local:8080'

def get_peers_count():
    # Use DNS resolution to dynamically get the count of pods in the StatefulSet
    # Load Kubernetes config (use in-cluster config if running inside the cluster)
    config.load_incluster_config()  # Use `config.load_kube_config()` for local testing
    
    # Define the namespace and StatefulSet name
    statefulset_name = "kvstore"
    
    # Initialize Kubernetes client
    v1_apps = kubernetes.client.AppsV1Api()

    # Get the StatefulSet information
    statefulset = v1_apps.read_namespaced_stateful_set(statefulset_name, namespace)
    
    # Return the number of replicas (e.g., 3 replicas)
    return statefulset.spec.replicas



    
@app.get("/")
def index():
    return {"ans": "It works!"}


@app.get("/context/get/{key}")
def get_key(key: str):
    """Retrieve the value associated with the key."""
    value = kv_store["context_dict"].get(key, None)
    return value

@app.get("/context/all_keys")
def get_all_keys():
    return {"keys": list(kv_store["context_dict"].keys())}

class ValueModel(BaseModel):
    context: str = Field(..., description="The chat context.")
    messages: list[dict] = Field(..., description="A list of chat messages.")
    tokens_used: int = Field(..., description="The number of tokens in the conversation")

@app.post("/context/set/{key}")
def set_key(key: str, body: ValueModel):
    """Set a key-value pair."""
    kv_store["context_dict"][key] = body
    return {"response": f"{key} successfully added"}

@app.get("/check")
def check():
    """Simple health check endpoint to confirm that the peer is up."""
    return {"status": "up"}

@app.get("/total_peer_count")
def total_peer_count():
    global peer_count
    peer_count = get_peers_count()
    return peer_count

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
