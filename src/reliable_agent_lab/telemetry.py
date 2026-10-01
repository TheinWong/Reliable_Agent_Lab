"""Minimal OTLP tracing setup for the local demo runtime."""

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_provider: TracerProvider | None = None


def get_tracer(name: str) -> trace.Tracer:
    if _provider is not None:
        return _provider.get_tracer(name)
    return trace.get_tracer(name)


def configure_tracing(service_name: str, endpoint: str | None) -> TracerProvider | None:
    global _provider
    if not endpoint:
        return None
    provider = TracerProvider(resource=Resource.create({SERVICE_NAME: service_name}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, timeout=5)))
    _provider = provider
    return provider
