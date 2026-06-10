with open("tracepilot/api.py", "r") as f:
    content = f.read()

content = content.replace(
    '        with ThreadPoolExecutor(max_workers=1) as executor:\n            future = executor.submit(_run_threaded_query, request.query)\n            result = future.result()\n        return {"status": "success", "response": result}',
    '        print(f"[DEBUG API] Received request.query: \'{request.query}\'")\n        with ThreadPoolExecutor(max_workers=1) as executor:\n            future = executor.submit(_run_threaded_query, request.query)\n            result = future.result()\n        print(f"[DEBUG API] Returning result: {str(result)[:200]}")\n        return {"status": "success", "response": result}'
)

with open("tracepilot/api.py", "w") as f:
    f.write(content)
