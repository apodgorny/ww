# ======================================================================
# TimePoint — unix timestamp wrapper.
# ======================================================================

from datetime import datetime, timezone

import o


class TimePoint(o.Schema):

	timestamp = o.F(int)

	# ----------------------------------------------------------------------
	def __str__(self):
		result = self.to_datetime().isoformat()
		return result

	# ----------------------------------------------------------------------
	def __repr__(self):
		result = str(self)
		return result

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Create from timestamp or instance
	# ----------------------------------------------------------------------
	@classmethod
	def create(cls, value):
		result = None

		if isinstance(value, cls) : result = value
		else                      : result = cls(timestamp=int(value))

		return result

	# Create from ISO string
	# ----------------------------------------------------------------------
	@classmethod
	def from_iso(cls, value):
		result = None
		parsed = None

		if value:
			candidates = [
				value,
				value.replace('Z', '+00:00')
			]

			for candidate in candidates:
				try              : parsed = datetime.fromisoformat(candidate)
				except Exception : parsed = None

				if parsed is not None:
					break

			if parsed is not None:
				result = cls(timestamp=int(parsed.timestamp()))

		return result


	# Convert to datetime
	# ----------------------------------------------------------------------
	def to_datetime(self, tz=timezone.utc):
		result = datetime.fromtimestamp(self.timestamp, tz=tz)
		return result
