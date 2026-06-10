"""TracePilot tracing setup — Arize Phoenix + OpenInference."""

import os
from tracepilot.config import PHOENIX_ENDPOINT, PROJECT_NAME


def init_tracing():
    """Initialize Phoenix tracing. Must be called BEFORE any agent code."""
    os.environ["PHOENIX_API_KEY"] = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJBcGlLZXk6MyJ9.G3anSj4kWc9mAw4tZ0hNj3I8cgUrYetmOhOI2kXBCtI"
    os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = PHOENIX_ENDPOINT + "/v1/traces"
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = "Authorization=Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJBcGlLZXk6MyJ9.G3anSj4kWc9mAw4tZ0hNj3I8cgUrYetmOhOI2kXBCtI"
    from phoenix.otel import register
    from openinference.instrumentation.google_adk import GoogleADKInstrumentor
    
    tracer_provider = register(
        project_name=PROJECT_NAME,
        endpoint=PHOENIX_ENDPOINT + "/v1/traces",
        auto_instrument=True,
    )
    GoogleADKInstrumentor().instrument(tracer_provider=tracer_provider)
    
    return tracer_provider
