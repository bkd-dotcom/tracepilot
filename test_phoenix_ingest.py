import os
from phoenix.otel import register

os.environ["PHOENIX_API_KEY"] = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJBcGlLZXk6MSJ9.bw5w46vTPfXxGuTqGjyj3gsUG2MsnZhVN07m70HI0WQ"

tp = register(project_name="tracepilot")
print("Tracer Provider configured successfully:", tp)
