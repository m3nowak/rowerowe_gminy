from rg_app.common.msg.base_model import BaseModel


class ProblemDetails(BaseModel):
    type: str
    status: int
    title: str | None
    detail: str | None
    instance: str | None
