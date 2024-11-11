def internal_cmd_activity_subject(type: str, athlete_id: int, activity_id: int | None = None) -> str:
    if activity_id is None:
        return f"rg.internal.cmd.activity.{type}.{athlete_id}"
    return f"rg.internal.cmd.activity.{type}.{athlete_id}.{activity_id}"
