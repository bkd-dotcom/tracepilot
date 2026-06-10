"""TracePilot configuration constants."""

# Model
MODEL_NAME = "gemini-1.5-flash"

# Tool costs (hardcoded for hackathon)
TOOL_COSTS = {
    "internal_kb": 0.01,   # $ per call
    "web_search": 0.12,     # $ per call
    "uploaded_documents": 0.005 # Extremely cheap and fast
}

# Normalization bounds for scoring
MAX_EXPECTED_COST = 0.25      # $ — upper bound for cost normalization
MAX_EXPECTED_LATENCY = 5.0    # seconds — upper bound for latency normalization

# Scoring weights
W_SUCCESS = 0.60
W_COST = 0.15
W_LATENCY = 0.10
W_RECOVERY = 0.15

# Routing
EXPLOIT_THRESHOLD = 0.5    # Below this, explore instead of exploit
DEFAULT_TOOL = "web_search"  # Naive default before learning

# Phoenix
PHOENIX_ENDPOINT = "https://app.phoenix.arize.com"
PROJECT_NAME = "tracepilot"
