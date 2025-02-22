from datetime import datetime

from .base import BaseStravaModel


class AthletePartial(BaseStravaModel):
    id: int
    created_at: datetime
