"""Mock tools for the TracePilot ADK agent."""

import json
import os
import time
import random

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def _load_kb() -> dict:
    with open(os.path.join(_DATA_DIR, "knowledge_base.json")) as f:
        return json.load(f)

def internal_kb_search(query: str) -> dict:
    """Search the internal enterprise knowledge base for company documents, policies, and employee information."""
    try:
        kb_data = _load_kb()
    except Exception as e:
        return {"status": "error", "source": "internal_kb", "error": f"Failed to load KB: {e}"}

    # Artificial latency removed

    query_lower = query.lower()
    for entry in kb_data.get("entries", []):
        for kw in entry.get("keywords", []):
            if kw.lower() in query_lower:
                return {
                    "status": "success", 
                    "source": "internal_kb", 
                    "title": entry["title"], 
                    "content": entry["content"]
                }
                
    return {
        "status": "error", 
        "source": "internal_kb", 
        "error": "No matching document found in internal knowledge base."
    }

def web_search(query: str) -> dict:
    """Simulates an expensive, slow web search."""
    
    # Removed artificial latency to make model work normally
    
    # Force a failure if it's an internal company query
    internal_keywords = ['handbook', 'pto', 'employee', 'policy']
        
    if any(word in query.lower() for word in internal_keywords):
        return {"status": "error", "source": "web_search", "error": "Access Denied: Internal data not found on public web."}
    
    # Generic success for public queries
    return {"status": "success", "data": f"Simulated web results for: {query}"}

def _load_uploaded_docs() -> list:
    path = os.path.join(_DATA_DIR, "uploaded_docs.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return []

def uploaded_documents_search(query: str) -> dict:
    """Search recently uploaded user documents and custom files."""
    docs = _load_uploaded_docs()
    if not docs:
        return {"status": "error", "source": "uploaded_documents", "error": "No uploaded documents available."}
        
    # Extremely fast since it's "local" memory
    pass
    
    query_lower = query.lower()
    for doc in docs:
        for kw in doc.get("keywords", []):
            if kw.lower() in query_lower:
                return {
                    "status": "success",
                    "source": "uploaded_documents",
                    "title": doc.get("title", "Uploaded Document"),
                    "content": doc.get("content", "")
                }
                
    return {
        "status": "error",
        "source": "uploaded_documents",
        "error": "No matching uploaded document found."
    }
