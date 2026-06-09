from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

# Import your existing TracePilot logic
from tracepilot.orchestrator import run_query
from tracepilot.auditor import run_audit
from tracepilot.memory import get_confidence_table, reset_db

app = FastAPI(title="TracePilot API")

# Mount the static directory for HTML/CSS/JS
static_dir = os.path.join(os.path.dirname(__file__), "static")
# Create static dir if it doesn't exist
os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

class QueryRequest(BaseModel):
    query: str

class UploadRequest(BaseModel):
    filename: str
    content: str

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/app")
async def serve_app():
    return FileResponse(os.path.join(static_dir, "app.html"))

@app.post("/api/upload")
def handle_upload(request: UploadRequest):
    import json
    import re
    from collections import Counter
    
    try:
        # Combine title and content for keyword extraction
        full_text = f"{request.filename} {request.content}".lower()
        # Extract alphanumeric words >= 3 characters
        words = re.findall(r'\b[a-zA-Z0-9]{3,}\b', full_text)
        # Exclude common stop words
        stop_words = {"this", "that", "with", "from", "your", "have", "they", "will", "would", "what", "when", "where", "which"}
        words = [w for w in words if w not in stop_words]
        
        # Get top 5 keywords, but ensure the title itself is heavily prioritized if it's a single word
        common_words = [word for word, count in Counter(words).most_common(5)]
        
        doc = {
            "title": request.filename,
            "content": request.content,
            "keywords": common_words
        }
        
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        file_path = os.path.join(data_dir, "uploaded_docs.json")
        
        docs = []
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                try:
                    docs = json.load(f)
                except json.JSONDecodeError:
                    pass
                    
        docs.append(doc)
        with open(file_path, "w") as f:
            json.dump(docs, f, indent=2)
            
        return {"status": "success", "message": "Document uploaded and indexed successfully.", "keywords": common_words}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/timeline")
def get_timeline():
    from tracepilot.events import get_events
    return get_events()

def _run_isolated_query(q: str):
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()
    from tracepilot.orchestrator import run_query
    return asyncio.run(run_query(q))

@app.post("/api/query")
def handle_query(request: QueryRequest):
    from concurrent.futures import ProcessPoolExecutor
    try:
        # Run in a completely isolated process to avoid Google ADK / httpx async conflicts
        with ProcessPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_isolated_query, request.query)
            result = future.result()
        return {"status": "success", "response": result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/audit")
async def handle_audit():
    try:
        # Calls your existing Phoenix telemetry scraper
        run_audit()
        # Fetch updated memory
        table_data = get_confidence_table()
        return {"status": "success", "message": "Audit complete. Memory updated.", "data": table_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memory")
async def get_memory():
    try:
        # Fetches the current SQLite table
        table_data = get_confidence_table()
        return {"status": "success", "data": table_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reset")
def reset_database():
    from tracepilot.events import clear_events
    import json
    try:
        reset_db()
        clear_events()
        
        # Clear uploaded docs
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        file_path = os.path.join(data_dir, "uploaded_docs.json")
        if os.path.exists(file_path):
            with open(file_path, "w") as f:
                json.dump([], f)
                
        return {"status": "success", "message": "Database reset"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents")
def get_documents():
    import json
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    file_path = os.path.join(data_dir, "uploaded_docs.json")
    if not os.path.exists(file_path):
        return {"status": "success", "data": []}
    try:
        with open(file_path, "r") as f:
            docs = json.load(f)
            # Remove the heavy 'content' payload if we just want to preview it, or truncate it
            for d in docs:
                if len(d.get("content", "")) > 100:
                    d["content"] = d["content"][:100] + "..."
            return {"status": "success", "data": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
