from dataclasses import dataclass
from logging import INFO, Formatter, Logger, getLogger
from typing import Awaitable, Callable
from urllib.parse import urljoin

from faststream import ContextRepo, Depends
from faststream.nats.opentelemetry import NatsTelemetryMiddleware
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv.attributes import service_attributes
from opentelemetry.trace import Tracer

from rg_app.common.config import BaseOtelConfig


@dataclass
class OtelBundle:
    on_startup: Callable[..., Awaitable[None]]
    middeware: NatsTelemetryMiddleware


def on_startup_factory(tracer_provider: TracerProvider, meter_provider: MeterProvider, otel_logger: Logger):
    async def on_startup(context: ContextRepo):
        context.set_global("tracer_provider", tracer_provider)
        context.set_global("meter_provider", meter_provider)
        context.set_global("otel_logger", otel_logger)

    return on_startup


def prepare_bundle(config: BaseOtelConfig):
    if not config.enabled:
        return None
    svc_name = config.svc_name or "rg-unnamed"
    svc_ns = config.svc_ns or "default"
    resource = Resource.create(attributes={service_attributes.SERVICE_NAME: svc_name, "service.namespace": svc_ns})

    tracer_prov = TracerProvider(resource=resource)
    trace_endpoint = urljoin(config.endpoint, "v1/traces")
    exporter = OTLPSpanExporter(endpoint=trace_endpoint)
    processor = BatchSpanProcessor(exporter)
    tracer_prov.add_span_processor(processor)

    metric_endpoint = urljoin(config.endpoint, "v1/metrics")
    otlp_metric_exporter = OTLPMetricExporter(endpoint=metric_endpoint)
    metric_reader = PeriodicExportingMetricReader(otlp_metric_exporter, export_interval_millis=1000)
    meter_prov = MeterProvider(metric_readers=[metric_reader], resource=resource)

    log_endpoint = urljoin(config.endpoint, "v1/logs")
    otlp_log_exporter = OTLPLogExporter(endpoint=log_endpoint)
    log_processor = BatchLogRecordProcessor(otlp_log_exporter)
    log_prov = LoggerProvider(resource=resource)
    log_prov.add_log_record_processor(log_processor)
    log_handler = LoggingHandler(level=INFO, logger_provider=log_prov)
    log_handler.setFormatter(Formatter("%(message)s"))
    logger = getLogger("rg-otel")

    logger.propagate = False
    logger.addHandler(log_handler)
    logger.setLevel(INFO)

    return OtelBundle(
        on_startup=on_startup_factory(tracer_provider=tracer_prov, meter_provider=meter_prov, otel_logger=logger),
        middeware=NatsTelemetryMiddleware(tracer_provider=tracer_prov, meter_provider=meter_prov),
    )


def tracer_provider(context: ContextRepo) -> TracerProvider:
    return context.get("tracer_provider")


def tracer_fn(tracer_provider: TracerProvider = Depends(tracer_provider)) -> Tracer:
    return tracer_provider.get_tracer("rg-app.faststream.otel")


def meter_provider(context: ContextRepo) -> MeterProvider:
    return context.get("meter_provider")


def meter_fn(meter_provider: MeterProvider = Depends(meter_provider)):
    return meter_provider.get_meter("rg-app.faststream.otel")


def otel_logger(context: ContextRepo) -> Logger:
    return getLogger("rg-otel")
