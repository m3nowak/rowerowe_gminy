from rg_app.common._config_base import BaseConfigStruct


class BaseOtelConfig(BaseConfigStruct):
    enabled: bool = True
    endpoint: str | None = None
    use_grpc: bool = True
    svc_name: str | None = None
    svc_ns: str | None = None
    extra_attrs: dict[str, int | str] | None = None

    def get_endpoint(self) -> str:
        if self.endpoint is None:
            if self.use_grpc:
                return "http://127.0.0.1:4317/"
            else:
                return "http://127.0.0.1:4318/"
        else:
            return self.endpoint