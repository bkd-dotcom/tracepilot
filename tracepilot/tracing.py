"""TracePilot tracing setup — Arize Phoenix + OpenInference."""

import os
from tracepilot.config import PHOENIX_ENDPOINT, PROJECT_NAME


def init_tracing():
    """Initialize Phoenix tracing. Must be called BEFORE any agent code."""
    os.environ.pop("PHOENIX_API_KEY", None)
    os.environ["PHOENIX_COLLECTOR_ENDPOINT"] = "http://127.0.0.1:6006/v1/traces"
    os.environ.pop("OTEL_EXPORTER_OTLP_HEADERS", None)
    
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    
    resource = Resource.create({"service.name": PROJECT_NAME})
    tracer_provider = TracerProvider(resource=resource)
    
    # Use SimpleSpanProcessor to force synchronous flush on every span (critical for Cloud Run)
    exporter = OTLPSpanExporter(endpoint="http://127.0.0.1:6006/v1/traces")
    processor = SimpleSpanProcessor(exporter)
    tracer_provider.add_span_processor(processor)
    
    trace.set_tracer_provider(tracer_provider)
    
    from openinference.instrumentation.google_adk import GoogleADKInstrumentor
    GoogleADKInstrumentor().instrument(tracer_provider=tracer_provider)
    
    return tracer_provider
