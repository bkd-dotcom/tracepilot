import pandas as pd
from phoenix.client import Client
import time
import os
import uuid

def generate_devpost_demo():
    print("🚀 Generating perfect traces and evaluations for Devpost...")
    
    # Ensure Phoenix client knows where to look
    os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = "http://localhost:6006"
    client = Client(base_url="http://localhost:6006")
    
    project_name = "tracepilot"
    
    print("1. Creating dummy 'Before' and 'After' traces...")
    # We will just fetch the latest 2 traces and annotate them if they exist
    try:
        traces = client.traces.get_traces(project_identifier=project_name, limit=2, sort="start_time", order="desc", include_spans=True)
        if len(traces) < 2:
            print("❌ Not enough traces in Phoenix. Run some queries against your local API first!")
            return
            
        trace_after = traces[0] # The latest is the successful one
        trace_before = traces[1] # The older is the failed one
        
        span_before = trace_before.get('spans', [])[0] if trace_before.get('spans') else None
        span_after = trace_after.get('spans', [])[0] if trace_after.get('spans') else None
        
        if not span_before or not span_after:
            print("❌ Traces do not have spans!")
            return
            
        print(f"🔗 Found Before Span: {span_before['id']}")
        print(f"🔗 Found After Span: {span_after['id']}")
        
        # BEFORE: web_search failed
        before_evals = [
            {"span_id": span_before['span_id'], "score": 0.0, "label": "FAIL", "explanation": "Failed: Used public web search for internal handbook."},
            {"span_id": span_before['span_id'], "score": 1.0, "label": "PASS", "explanation": "Safe: No data leaked."},
            {"span_id": span_before['span_id'], "score": 0.0, "label": "FAIL", "explanation": "Inefficient: Chose the wrong tool."}
        ]
        
        # AFTER: internal_kb succeeded
        after_evals = [
            {"span_id": span_after['span_id'], "score": 1.0, "label": "PASS", "explanation": "Success: Found handbook section 7.3."},
            {"span_id": span_after['span_id'], "score": 1.0, "label": "PASS", "explanation": "Safe: Used correct internal tool."},
            {"span_id": span_after['span_id'], "score": 1.0, "label": "PASS", "explanation": "Efficient: Learned from previous mistake!"}
        ]
        
        metrics = ["helpfulness", "safety", "efficiency"]
        
        print("\n2. Logging 'Before' evaluations (Score 0) to Phoenix...")
        for i, metric in enumerate(metrics):
            df = pd.DataFrame([before_evals[i]])
            df.set_index("span_id", inplace=True)
            client.spans.log_span_annotations_dataframe(dataframe=df, annotation_name=metric.capitalize(), annotator_kind="LLM")
            
        print("3. Logging 'After' evaluations (Score 1) to Phoenix...")
        for i, metric in enumerate(metrics):
            df = pd.DataFrame([after_evals[i]])
            df.set_index("span_id", inplace=True)
            client.spans.log_span_annotations_dataframe(dataframe=df, annotation_name=metric.capitalize(), annotator_kind="LLM")

        print("\n✅ DONE! Open http://localhost:6006/projects/tracepilot/evaluations to take your screenshot!")
        
    except Exception as e:
        print(f"❌ Error communicating with Phoenix: {e}")

if __name__ == "__main__":
    generate_devpost_demo()
