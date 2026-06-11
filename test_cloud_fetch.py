import os
import httpx
from phoenix.client import Client

os.environ.pop("PHOENIX_COLLECTOR_ENDPOINT", None)

os.environ["PHOENIX_API_KEY"] = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJBcGlLZXk6MSJ9.bw5w46vTPfXxGuTqGjyj3gsUG2MsnZhVN07m70HI0WQ"
os.environ["PHOENIX_CLIENT_HEADERS"] = "api_key=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJBcGlLZXk6MSJ9.bw5w46vTPfXxGuTqGjyj3gsUG2MsnZhVN07m70HI0WQ"

client = Client(base_url="https://app.phoenix.arize.com/graphql")
try:
    df = client.spans.get_spans_dataframe(project_name="tracepilot")
    print("Found spans with /graphql!", len(df))
except Exception as e:
    print("Failed with endpoint /graphql:", type(e), str(e))

client2 = Client(base_url="https://app.phoenix.arize.com")
try:
    df = client2.spans.get_spans_dataframe(project_name="tracepilot")
    print("Found spans with base!", len(df))
except Exception as e:
    print("Failed with endpoint base:", type(e), str(e))
