from rg_app.common.enums import DescUpdateOptions
from rg_app.common.msg.base_model import BaseModel


class UserSettings(BaseModel):
    update_strava_desc: DescUpdateOptions


class UserSettingsPartial(BaseModel):
    update_strava_desc: DescUpdateOptions | None = None
