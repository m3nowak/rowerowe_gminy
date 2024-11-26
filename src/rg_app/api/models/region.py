from datetime import datetime

from rg_app.common.msg.base_model import BaseModel


class LastVisitResponse(BaseModel):
    visit: datetime | None
