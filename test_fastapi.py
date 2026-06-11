from fastapi import FastAPI
import asyncio
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/")
def test_sync():
    try:
        loop = asyncio.get_running_loop()
        return "Loop is running"
    except RuntimeError:
        return "No loop running"

client = TestClient(app)
print(client.get("/").json())
