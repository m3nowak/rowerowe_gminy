from logging import INFO, Formatter, Logger, getLogger
from urllib.parse import urljoin

from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter as GRPCLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter as GRPCMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as GRPCSpanExporter
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter as HTTPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter as HTTPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HTTPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .config import BaseOtelConfig

LIBRARY_NAME = "rowerowe-gminy-utils-otel"


def prepare_utils(config: BaseOtelConfig) -> tuple[MeterProvider, TracerProvider, Logger]:
    svc_name = config.svc_name or "rg-unnamed"
    svc_ns = config.svc_ns or "default"
    extra_attrs = config.extra_attrs or {}

    resource = Resource(
        attributes={
            "service.name": svc_name,
            "service.namespace": svc_ns,
            **extra_attrs,
        }
    )

    endpoint = config.get_endpoint()

    if config.enabled:
        if config.use_grpc:
            trace_endpoint = endpoint
            otlp_span_exporter = GRPCSpanExporter(endpoint=trace_endpoint, insecure=True)
        else:
            trace_endpoint = urljoin(endpoint, "/v1/traces")
            otlp_span_exporter = HTTPSpanExporter(endpoint=trace_endpoint)
        span_processor = BatchSpanProcessor(otlp_span_exporter)
        tracer_prov = TracerProvider(resource=resource)
        tracer_prov.add_span_processor(span_processor)
    else:
        tracer_prov = TracerProvider()  # I do nothing!

    if config.enabled:
        if config.use_grpc:
            metric_endpoint = endpoint
            otlp_metric_exporter = GRPCMetricExporter(endpoint=metric_endpoint, insecure=True)
        else:
            metric_endpoint = endpoint
            otlp_metric_exporter = HTTPMetricExporter(endpoint=metric_endpoint)
        metric_reader = PeriodicExportingMetricReader(otlp_metric_exporter, export_interval_millis=60000)
        meter_prov = MeterProvider(metric_readers=[metric_reader], resource=resource)
    else:
        meter_prov = MeterProvider()  # I do nothing!

    if config.enabled:
        if config.use_grpc:
            log_endpoint = endpoint
            otlp_log_exporter = GRPCLogExporter(endpoint=log_endpoint, insecure=True)
        else:
            log_endpoint = urljoin(endpoint, "/v1/logs")
            otlp_log_exporter = HTTPLogExporter(endpoint=log_endpoint)
        log_processor = BatchLogRecordProcessor(otlp_log_exporter)
        log_prov = LoggerProvider(resource=resource)
        log_prov.add_log_record_processor(log_processor)
        log_handler = LoggingHandler(level=INFO, logger_provider=log_prov)
        log_handler.setFormatter(Formatter("%(message)s"))
        logger = getLogger(LIBRARY_NAME)
        logger.propagate = False
        logger.addHandler(log_handler)
        logger.setLevel(INFO)
    else:
        logger = getLogger(LIBRARY_NAME)
        logger.propagate = False
        logger.setLevel(INFO)  # I do nothing!
    return meter_prov, tracer_prov, logger
