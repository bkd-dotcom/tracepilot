import fastapi
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

# Import your existing TracePilot logic
from tracepilot.orchestrator import run_query
from tracepilot.auditor import run_audit
from tracepilot.memory import get_confidence_table, reset_db
from tracepilot.tracing import init_tracing

# Initialize tracing globally once when the FastAPI server starts
init_tracing()

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    import phoenix as px
    import os
    os.environ["PHOENIX_PORT"] = "6006"
    px.launch_app(use_temp_dir=False)
    yield

app = FastAPI(title="TracePilot API", lifespan=lifespan)

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
        stop_words = {"this", "that", "with", "from", "your", "have", "they", "will", "would", "what", "when", "where", "which", "and", "for", "the", "are", "is", "it", "you"}
        words = [w for w in words if w not in stop_words]
        
        # Get top 5 keywords
        common_words = [word for word, count in Counter(words).most_common(5)]
        
        # Ensure filename base words are ALWAYS included as keywords
        base_name = request.filename.lower().split('.')[0]
        base_words = re.findall(r'\b[a-zA-Z0-9]{3,}\b', base_name)
        for bw in base_words:
            if bw not in common_words and bw not in stop_words:
                common_words.insert(0, bw)
        
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

def _run_threaded_query(q: str):
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()
    
    from tracepilot.orchestrator import run_query
    result = asyncio.run(run_query(q))
    
    # Force flush so traces are immediately available in Phoenix
    from opentelemetry import trace
    provider = trace.get_tracer_provider()
    if hasattr(provider, 'force_flush'):
        provider.force_flush()
        
    return result

@app.post("/api/query")
def handle_query(request: QueryRequest):
    from concurrent.futures import ThreadPoolExecutor
    try:
        print(f"[DEBUG API] Received request.query: '{request.query}'")
        # Run the ADK agent query in a dedicated thread
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_threaded_query, request.query)
            result = future.result()

        # Step 1.5: Give Uvicorn/OTel a brief moment to flush the traces synchronously 
        import time
        time.sleep(0.3)
        
        print(f"[DEBUG API] Returning result: {str(result)[:200]}")
        return {"status": "success", "response": result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/evaluate_jury")
async def evaluate_jury():
    """Triggered by the frontend immediately after a query returns."""
    import time
    # Sleep to ensure Phoenix ingestion worker finishes writing to SQLite before we query it
    time.sleep(3.0)
    try:
        from tracepilot.evaluator import run_evaluations
        run_evaluations()
        return {"status": "success"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@app.post("/api/audit")
async def handle_audit(background_tasks: fastapi.BackgroundTasks = None):
    try:
        from tracepilot.auditor import async_run_audit
        from tracepilot.memory import get_confidence_table, _recalculate_all
        from rich.console import Console
        from tracepilot.display import print_audit_summary, print_confidence_table
        from tracepilot.events import emit_event
        from tracepilot.evaluator import async_run_evaluations
        
        console = Console()
        db_path = "tracepilot_memory.db"
        before = get_confidence_table(db_path)
        
        corrections_made = await async_run_audit(db_path)
        
        if corrections_made > 0:
            console.print(f"[yellow]⚠️ MCP Audit found {corrections_made} hidden tool failures! Correcting memory...[/yellow]")
            emit_event(
                type="learning",
                title="Memory Correction",
                description=f"MCP Auditor Agent found {corrections_made} hidden LLM failure(s). Confidence scores recalculated.",
                metrics={"corrections": corrections_made}
            )
        else:
            console.print("[green]✅ MCP Audit complete. No new hidden tool failures found.[/green]")
            
        console.print("[dim]Recalculating confidence scores from run history...[/dim]\n")
        _recalculate_all(db_path)
        after = get_confidence_table(db_path)
        print_audit_summary(before, after)
        console.print("\n[bold]Current Economic Memory:[/bold]")
        print_confidence_table(after)
        
        # Cloud Run freezes CPU after response, must evaluate synchronously
        try:
            console.print("[dim]Starting LLM Jury Evaluation...[/dim]")
            await async_run_evaluations()
        except Exception as e:
            console.print(f"[red]Error in Jury Eval: {e}[/red]")
        
        return {"status": "success", "message": "Audit complete. Memory updated. Jury evaluations completed.", "data": after}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

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

@app.get("/api/traces")
def get_traces():
    from tracepilot.config import PROJECT_NAME, PHOENIX_ENDPOINT
    from tracepilot.memory import get_last_reset_time
    import pandas as pd
    try:
        import sqlite3
        import os
        import json
        
        db_path = os.path.expanduser("~/.phoenix/phoenix.db")
        if not os.path.exists(db_path):
            return {"status": "success", "data": []}
            
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query("""
                SELECT span_id, name, start_time, end_time, attributes, span_kind 
                FROM spans 
                WHERE span_kind = 'TOOL' OR name LIKE 'execute_tool%'
            """, conn)
            
        if df is None or df.empty:
            return {"status": "success", "data": []}
            
        df['start_time'] = pd.to_datetime(df['start_time'], utc=True, errors='coerce')
        df = df.sort_values(by="start_time")
        recent = df.tail(15).fillna("").to_dict(orient="records")
        
        clean_data = []
        for r in recent:
            attributes_str = r.get("attributes", "{}")
            try:
                attributes = json.loads(attributes_str) if isinstance(attributes_str, str) else (attributes_str or {})
            except Exception:
                attributes = {}
            
            # output.value is a JSON string — parse it to check for errors
            output_wrapper = attributes.get("output", {})
            output_val_raw = output_wrapper.get("value", "") if isinstance(output_wrapper, dict) else str(output_wrapper)
            try:
                inner = json.loads(output_val_raw) if output_val_raw else {}
                status = "Error" if inner.get("status") == "error" or "error" in inner.get("type", "").lower() else "Success"
            except Exception:
                # Fallback: string search
                status = "Error" if '"status": "error"' in output_val_raw or "error" in output_val_raw.lower()[:60] else "Success"

            # Check span-level error flag
            if attributes.get("error", {}).get("type"):
                status = "Error"
            
            tool_name = str(attributes.get("tool", {}).get("name", ""))
            if not tool_name:
                tool_name = str(r.get("name", "Unknown")).replace("execute_tool ", "")
            
            # Calculate latency from timestamps
            start_t = r.get("start_time")
            end_t = r.get("end_time")
            latency_sec = 0.0
            if pd.notnull(start_t) and pd.notnull(end_t):
                end_dt = pd.to_datetime(end_t, utc=True)
                latency_sec = (end_dt - start_t).total_seconds()
                
            clean_data.append({
                "name": tool_name,
                "status": status,
                "latency": round(latency_sec, 3),
                "time": str(start_t)[:19] if pd.notnull(start_t) else ""
            })
        
        return {"status": "success", "data": clean_data[::-1]}
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Exception in get_traces: {e}")
        return {"status": "error", "data": []}
