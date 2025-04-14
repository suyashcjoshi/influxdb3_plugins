from fastapi import FastAPI, HTTPException
import redis
import json

app = FastAPI()

r = redis.Redis(host="host.docker.internal", port=6379, decode_responses=True)

@app.get("/analytics/{table}")
async def get_analytics(database: str, table: str):
    key = f"{table}"
    
    data = r.get(key)
    print(key)
    if data:
        return json.loads(data)  
    else:
        raise HTTPException(status_code=404, detail=f"No data found for {key}")

