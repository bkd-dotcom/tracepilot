"""TracePilot tracing setup — Arize Phoenix + OpenInference."""

import os
from tracepilot.config import PHOENIX_ENDPOINT, PROJECT_NAME


def init_tracing():
    """Initialize Phoenix tracing. Must be called BEFORE any agent code."""
    os.environ.pop("PHOENIX_API_KEY", None)
    os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = "http://127.0.0.1:6006/v1/traces"
    os.environ.pop("OTEL_EXPORTER_OTLP_HEADERS", None)
    from phoenix.otel import register
    from openinference.instrumentation.google_adk import GoogleADKInstrumentor
    
    tracer_provider = register(
        project_name=PROJECT_NAME,
        endpoint="http://127.0.0.1:6006/v1/traces",
        auto_instrument=True,
    )
    GoogleADKInstrumentor().instrument(tracer_provider=tracer_provider)
    
    return tracer_provider
