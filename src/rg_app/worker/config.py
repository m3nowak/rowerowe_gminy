from rg_app.common.config import BaseConfigStruct, BaseNatsConfig


class Config(BaseConfigStruct):
    nats: BaseNatsConfig
