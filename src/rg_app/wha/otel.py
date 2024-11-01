import uuid
from logging import INFO, Formatter, Logger, getLogger
from typing import Any, Sequence
from urllib.parse import urljoin

from litestar.config.app import AppConfig
from litestar.contrib.opentelemetry import OpenTelemetryConfig, OpenTelemetryPlugin
from litestar.di import Provide
from litestar.plugins import InitPluginProtocol
from litestar.types import Scope
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.metrics import Meter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.trace import Tracer

from rg_app.common.config import BaseOtelConfig

DI_KEY_METER_PROVIDER = "meter"
DI_KEY_TRACER_PROVIDER = "tracer"
DI_KEY_OTEL_LOGGER = "otel_logger"
DI_KEY_CORRELATION_ID = "correlation_id"


def _get_route_details_from_scope(scope: Scope) -> tuple[str, dict[Any, str]]:
    """Retrieve the span name and attributes from the ASGI scope.

    Args:
        scope: The ASGI scope instance.

    Returns:
        A tuple of the span name and a dict of attrs.
    """

    path = scope.get("path", "").strip()
    method = str(scope.get("method", "")).strip()
    headers = scope.get("headers", [])
    cid = None
    for k, v in headers:
        if k == b"x-correlation-id":
            cid = uuid.UUID(v.decode())
            break
    if cid is None:
        cid = uuid.uuid4()

    if method and path:  # http
        return f"{method} {path}", {SpanAttributes.HTTP_ROUTE: f"{method} {path}", "CID": cid.hex}

    return path, {SpanAttributes.HTTP_ROUTE: path}  # websocket


def prepare_plugins(config: BaseOtelConfig) -> Sequence[InitPluginProtocol]:
    if not config.enabled:
        return []
    svc_name = config.svc_name or "rg-unnamed"
    svc_ns = config.svc_ns or "default"

    resource = Resource(
        attributes={
            "service.name": svc_name,
            "service.namespace": svc_ns,
        }
    )

    endpoint = config.endpoint or "http://localhost:4318"

    trace_endpoint = urljoin(endpoint, "v1/traces")
    otlp_span_exporter = OTLPSpanExporter(endpoint=trace_endpoint)
    span_processor = BatchSpanProcessor(otlp_span_exporter)
    tracer_prov = TracerProvider(resource=resource)
    tracer_prov.add_span_processor(span_processor)

    metric_endpoint = urljoin(endpoint, "v1/metrics")
    otlp_metric_exporter = OTLPMetricExporter(endpoint=metric_endpoint)
    metric_reader = PeriodicExportingMetricReader(otlp_metric_exporter, export_interval_millis=1000)
    meter_prov = MeterProvider(metric_readers=[metric_reader], resource=resource)

    log_endpoint = urljoin(endpoint, "v1/logs")
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

    otel_config = OpenTelemetryConfig(
        meter_provider=meter_prov,
        tracer_provider=tracer_prov,
        scope_span_details_extractor=_get_route_details_from_scope,
    )
    otel_plugin = OpenTelemetryPlugin(otel_config)

    otel_sup_plugin = OtelSuplementalPlugin(config, meter_prov, tracer_prov, logger)

    return otel_plugin, otel_sup_plugin


class OtelSuplementalPlugin(InitPluginProtocol):
    def __init__(
        self,
        config: BaseOtelConfig,
        meter_provider: MeterProvider,
        tracer_provider: TracerProvider,
        logger: Logger,
    ):
        self.config = config
        self.meter_provider = meter_provider
        self.tracer_provider = tracer_provider
        self.logger = logger

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        def meter_fn() -> Meter:
            return self.meter_provider.get_meter("opentelemetry.instrumentation.rg-app")

        def tracer_fn() -> Tracer:
            return self.tracer_provider.get_tracer("opentelemetry.instrumentation.rg-app")

        def logger_fn() -> Logger:
            return self.logger

        # def correlation_id_fn(request: Request) -> str:
        #     cid = request.headers.get("X-Correlation-ID") or request.headers.get("correlation-id")

        #     if cid:
        #         return uuid.UUID(cid).hex
        #     else:
        #         return uuid.uuid4().hex

        app_config.dependencies[DI_KEY_METER_PROVIDER] = Provide(meter_fn, sync_to_thread=False)
        app_config.dependencies[DI_KEY_TRACER_PROVIDER] = Provide(tracer_fn, sync_to_thread=False)
        app_config.dependencies[DI_KEY_OTEL_LOGGER] = Provide(logger_fn, sync_to_thread=False)
        # app_config.dependencies[DI_KEY_CORRELATION_ID] = Provide(correlation_id_fn, sync_to_thread=False)

        return app_config
