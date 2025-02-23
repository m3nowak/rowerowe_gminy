from datetime import datetime

from rg_app.common.msg.base_model import BaseModel


class AthleteDetail(BaseModel):
    id: int
    created_at: datetime
