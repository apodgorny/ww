# ======================================================================
# TimeRange — unix timestamp interval.
# ======================================================================

import o


class TimeRange(o.Schema):

	start = o.F(int)
	end   = o.F(int)

	# ----------------------------------------------------------------------
	def __str__(self):

		result = f'[{self.start}, {self.end}]'
		return result


	# ----------------------------------------------------------------------
	def __repr__(self):

		result = str(self)
		return result


	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Check if timestamp is inside range
	# ----------------------------------------------------------------------
	def contains(self, ts):

		point  = o.T.TimePoint.create(ts)
		result = self.start <= point.timestamp <= self.end

		return result


	# Create range from values
	# ----------------------------------------------------------------------
	@classmethod
	def create(cls, from_value, to_value):

		start  = o.T.TimePoint.create(from_value).timestamp
		end    = o.T.TimePoint.create(to_value).timestamp
		result = cls(start=start, end=end)

		return result


	# Normalize input values
	# ----------------------------------------------------------------------
	@classmethod
	def on_create(cls, data):

		result = data

		if isinstance(result, dict):

			start = result.get('start')
			end   = result.get('end')

			if start is not None:
				result['start'] = o.T.TimePoint.create(start).timestamp

			if end is not None:
				result['end'] = o.T.TimePoint.create(end).timestamp

		return result
