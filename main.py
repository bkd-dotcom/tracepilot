import uvicorn

if __name__ == "__main__":
    print("🚀 Starting TracePilot API on http://localhost:8080...")
    uvicorn.run("tracepilot.api:app", host="0.0.0.0", port=8080, reload=True)
