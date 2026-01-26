# ======================================================================
# Time range schema for timestamp bounds.
# ======================================================================
# Usage example:
# tr = TimeRangeSchema.create(1700000000, 1700003600)
# print(tr.contains(1700001200))

from typing import Union

from wordwield.core.o import O


class TimeRangeSchema(O):
	start : int = O.Field(description='Range start (unix seconds)', llm=False, semantic=True)
	end   : int = O.Field(description='Range end (unix seconds)',   llm=False, semantic=True)

	# Format a readable range.
	# ----------------------------------------------------------------------
	def __str__(self):
		result = f'[{self.start}, {self.end}]'
		return result

	# Format a debug-friendly range.
	# ----------------------------------------------------------------------
	def __repr__(self):
		result = str(self)
		return result

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Check if a timestamp is within the range.
	# ----------------------------------------------------------------------
	def contains(self, ts: Union[int, 'TimePointSchema']) -> bool:
		point  = self.ww.schemas.TimePointSchema.create(ts)
		result = self.start <= point.timestamp <= self.end
		return result

	# Create a range from timestamps or time points.
	# ----------------------------------------------------------------------
	@classmethod
	def create(cls, from_value, to_value) -> 'TimeRangeSchema':
		start  = cls.ww.schemas.TimePointSchema.create(from_value).timestamp
		end    = cls.ww.schemas.TimePointSchema.create(to_value).timestamp
		result = cls(start=start, end=end)
		return result

	# Normalize range inputs before validation.
	# ----------------------------------------------------------------------
	@classmethod
	def on_create(cls, data):
		result = data
		if isinstance(result, dict):
			start = result.get('start')
			end   = result.get('end')
			if start is not None:
				result['start'] = cls.ww.schemas.TimePointSchema.create(start).timestamp
			if end is not None:
				result['end'] = cls.ww.schemas.TimePointSchema.create(end).timestamp
		return result
