import os
from phoenix.client import Client

os.environ["PHOENIX_API_KEY"] = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJBcGlLZXk6MSJ9.bw5w46vTPfXxGuTqGjyj3gsUG2MsnZhVN07m70HI0WQ"
os.environ.pop("PHOENIX_COLLECTOR_ENDPOINT", None)

client = Client()
print(client.spans.get_spans_dataframe(project_name="tracepilot"))
