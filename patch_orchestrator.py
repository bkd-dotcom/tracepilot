with open("tracepilot/orchestrator.py", "r") as f:
    content = f.read()

content = content.replace(
    'agent = _create_agent(tool_func)\n    \n    # Force the LLM to call the tool by appending an explicit instruction to the user\'s query\n    forced_query = query + "\\n\\n(System Instruction: You MUST call your provided tool. Never refuse to call it.)"\n    \n    # OVERRIDE FOR INTERNAL DATA VERBATIM EXPECTATION',
    'agent = _create_agent(tool_func)\n    \n    # Force the LLM to call the tool by appending an explicit instruction to the user\'s query\n    forced_query = query + "\\n\\n(System Instruction: You MUST call your provided tool. Never refuse to call it.)"\n    print(f"[DEBUG] Executing run_query with query=\'{query}\', selected_tool=\'{selected_tool}\'")\n    \n    # OVERRIDE FOR INTERNAL DATA VERBATIM EXPECTATION'
)

content = content.replace(
    '        if tool_result.get("status") == "success":\n            result_text = tool_result.get("content", "")\n            success = True\n        else:\n            result_text = f"TOOL_ERROR: {tool_result.get(\'error\', \'Unknown Error\')}"\n            success = False',
    '        if tool_result.get("status") == "success":\n            result_text = tool_result.get("content", "")\n            success = True\n            print(f"[DEBUG] Verbatim tool success. Output: {result_text[:50]}...")\n        else:\n            result_text = f"TOOL_ERROR: {tool_result.get(\'error\', \'Unknown Error\')}"\n            success = False\n            print(f"[DEBUG] Verbatim tool failure. Output: {result_text}")'
)

content = content.replace(
    '    try:\n        result_text, success = await _run_agent(agent, forced_query)\n    except Exception as e:',
    '    try:\n        print(f"[DEBUG] Calling ADK _run_agent with forced_query=\'{forced_query}\'")\n        result_text, success = await _run_agent(agent, forced_query)\n        print(f"[DEBUG] ADK returned result_text=\'{result_text}\', success={success}")\n    except Exception as e:'
)

with open("tracepilot/orchestrator.py", "w") as f:
    f.write(content)
