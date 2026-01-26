# ======================================================================
# Time point schema for timestamp utilities.
# ======================================================================
# Usage example:
# tp = TimePointSchema(timestamp=1700000000)
# print(tp.to_datetime())
# print(str(tp))

from datetime import datetime, timezone
from typing   import Optional

from wordwield.core.o import O


class TimePointSchema(O):
	timestamp : int = O.Field(description='Unix timestamp (seconds)', llm=False, semantic=True)

	# Format a readable time point.
	# ----------------------------------------------------------------------
	def __str__(self):
		result = self.to_datetime().isoformat()
		return result

	# Format a debug-friendly time point.
	# ----------------------------------------------------------------------
	def __repr__(self):
		result = str(self)
		return result

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Create a time point from timestamp or time point.
	# ----------------------------------------------------------------------
	@classmethod
	def create(cls, value) -> 'TimePointSchema':
		if isinstance(value, TimePointSchema):
			result = value
		else:
			result = cls(timestamp=int(value))
		return result

	# Create a time point from an ISO timestamp string.
	# ----------------------------------------------------------------------
	@classmethod
	def from_iso(cls, value) -> Optional['TimePointSchema']:
		result = None
		if value:
			candidates = [
				value,
				value.replace('Z', '+00:00')
			]
			parsed = None
			for candidate in candidates:
				try:
					parsed = datetime.fromisoformat(candidate)
				except Exception:
					parsed = None
				if parsed is not None:
					break
			if parsed is not None:
				result = cls(timestamp=int(parsed.timestamp()))
		return result

	# Convert a timestamp to datetime.
	# ----------------------------------------------------------------------
	def to_datetime(self, tz=timezone.utc) -> datetime:
		result = datetime.fromtimestamp(self.timestamp, tz=tz)
		return result
