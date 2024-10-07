from datetime import UTC

from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator


# Custom TypeDecorator for DateTime
class UTCDateTime(TypeDecorator):
    """Custom DateTime type that assumes naive datetime is UTC when loaded from DB."""
    
    impl = DateTime  # Underlying column type is DateTime

    # Customize how Python datetime objects are bound to the DB
    def process_bind_param(self, value, dialect):
        if value is not None:
            # Ensure the datetime is naive (i.e., without timezone info) before storing it
            if value.tzinfo is not None:
                value = value.astimezone(UTC).replace(tzinfo=None)
        return value

    # Customize how DB datetime values are returned to Python objects
    def process_result_value(self, value, dialect):
        if value is not None:
            # Assume the naive datetime from the DB is in UTC and return a timezone-aware datetime
            return value.replace(tzinfo=UTC)
        return value