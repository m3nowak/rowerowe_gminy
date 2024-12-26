from rg_app.common.strava.activities import ActivityPartial

RIDE_LIKE_TYPES = {
    "EBikeRide",
    "EMountainBikeRide",
    "GravelRide",
    "Handcycle",
    "MountainBikeRide",
    "Ride",
    "Velomobile",
    "Wheelchair",
}


def activity_filter(activity: ActivityPartial) -> tuple[bool, str | None]:
    utype = activity.sport_type
    if utype not in RIDE_LIKE_TYPES:
        return False, f"Activity type {activity.sport_type} is not supported"
    if activity.map is None or (activity.map.summary_polyline is None and activity.map.polyline is None):
        return False, "Activity has no map"
    if activity.distance is None or activity.distance == 0:
        return False, "Activity has no distance"

    return True, None
