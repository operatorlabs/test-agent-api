from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from datetime import datetime
from dotenv import load_dotenv
import os
import requests
import time

app = FastAPI()
load_dotenv()

# For custom whitelist logic
neynar_key = os.environ.get("NEYNAR_SQL_API_KEY")

class Item(BaseModel):
    message: str

"""
Check whether a given address is registered on Farcaster or not.
If yes, then they are approved for the whitelist.

Parameters:
address: Ethereum address starting with 0x

Returns:
true or false
"""
def check_whitelist(address: str) -> bool:
    url = 'https://data.hubs.neynar.com/api/queries/257/results'
    params = {'api_key': neynar_key}
    payload = {
        "max_age": 1800,
        "parameters": {
            "address": address.strip().lower()
        }
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, params=params, headers=headers, json=payload).json()
    if "query_result" not in list(response.keys()):
        if "job" not in list(response.keys()):
            raise ValueError("Error while trying to find matches. Is your API key valid?")
        else:
            time.sleep(1)
            response = requests.post(url, params=params, headers=headers, json=payload).json()
            if "query_result" not in list(response.keys()):
                raise ValueError("Error while trying to find matches. Is your API key valid?")
                
    rows = response["query_result"]["data"]["rows"]
    return len(rows) > 0

@app.post("/entrypoint")
async def read_item(request: Request, item: Item):
    # Verify that the sender header is present
    sender = request.headers.get('Sender')
    if not sender:
        raise HTTPException(status_code=400, detail="Sender header is required")
    elif not sender.startswith("0x"):
        raise HTTPException(status_code=400, detail="Sender address should start with 0x")
    elif len(sender) != 42:
        raise HTTPException(status_code=400, detail="Sender address must be a valid Ethereum address")


    # With the sender address, now you can do any sort of validation you want
    if not check_whitelist(sender):
        raise HTTPException(status_code=400, detail="Address not in whitelist")

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {"message": f"Got message at {current_time} from {sender}: {item.message}"}

# curl -X POST "http://localhost:8000/entrypoint" -H  "accept: application/json" -H  "Content-Type: application/json" -d '{"message":"Hello, World!"}'