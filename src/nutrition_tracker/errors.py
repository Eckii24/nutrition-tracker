class NutritionTrackerError(Exception):
    """Base domain error."""


class ValidationError(NutritionTrackerError):
    """Payload or storage validation failed."""


class NotFoundError(NutritionTrackerError):
    """Requested object does not exist."""


class StorageError(NutritionTrackerError):
    """Storage operation failed."""
