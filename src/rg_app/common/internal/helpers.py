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
        return False, "BAD_TYPE"
    if activity.map is None or (not activity.map.summary_polyline and not activity.map.polyline):
        return False, "NO_MAP"
    if activity.distance is None or activity.distance == 0:
        return False, "NO_DISTANCE"

    return True, None
