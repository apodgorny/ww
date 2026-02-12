# ======================================================================
# Gulp — single stream event.
# ======================================================================

from time import time

import o


class Gulp(o.Schema):
	timestamp = o.F(int)
	value     = o.F(str)
	author    = o.F(str)

	# ----------------------------------------------------------------------
	def __str__(self):
		result = f'Gulp [{self.timestamp}] {self.author}: "{self.value}"'
		return result

	# ----------------------------------------------------------------------
	def __repr__(self):
		result = str(self)
		return result

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Normalize timestamp on create
	# ----------------------------------------------------------------------
	@classmethod
	def on_create(cls, data):
		if 'timestamp' not in data or data['timestamp'] is None:
			data['timestamp'] = int(time() * 1000)

		return data

	# Convert to prompt format
	# ----------------------------------------------------------------------
	def to_prompt(self):
		result = f'[{self.author}]: "{self.value}"'
		return result
