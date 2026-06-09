"""TracePilot tracing setup — Arize Phoenix + OpenInference."""

import os
from tracepilot.config import PHOENIX_ENDPOINT, PROJECT_NAME


def init_tracing():
    """Initialize Phoenix tracing. Must be called BEFORE any agent code."""
    # Set environment variable for Phoenix endpoint
    os.environ.setdefault("PHOENIX_COLLECTOR_ENDPOINT", PHOENIX_ENDPOINT)
    
    from phoenix.otel import register
    from openinference.instrumentation.google_adk import GoogleADKInstrumentor
    
    tracer_provider = register(
        project_name=PROJECT_NAME,
        auto_instrument=True,
    )
    GoogleADKInstrumentor().instrument(tracer_provider=tracer_provider)
    
    return tracer_provider
