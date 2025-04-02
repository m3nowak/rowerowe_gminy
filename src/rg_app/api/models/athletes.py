from datetime import datetime

from rg_app.common.msg.base_model import BaseModel


class AthleteDetail(BaseModel):
    id: int
    created_at: datetime
    last_backlog_sync: datetime | None
    backlog_sync_eligible: bool
    strava_account_created_at: datetime
    unprocessed_activities: int
