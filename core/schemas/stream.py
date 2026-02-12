# ======================================================================
# Stream — ordered sequence of gulps.
# ======================================================================

import os

import o
from wordwield import ww


class Stream(o.Schema):
	name      = o.F(str)
	role      = o.F(str)
	gulps     = o.F(list[Gulp], default_factory=list)
	author    = o.F(str)
	is_zipped = False

	# ----------------------------------------------------------------------
	def __len__(self):
		result = len(self.gulps or [])
		return result

	# ======================================================================
	# PRIVATE METHODS
	# ======================================================================

	# Create substream from gulps
	# ----------------------------------------------------------------------
	def _gulps_to_stream(self, gulps):
		result = Stream(
			name   = self.name,
			role   = self.role,
			gulps  = gulps,
			author = self.author
		)
		return result

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Zip multiple streams
	# ----------------------------------------------------------------------
	@classmethod
	def zip(cls, *names):
		gulps = []

		for name in names:
			if stream := cls.load(name):
				for g in stream.gulps or []:
					gulps.append(g.clone())

		gulps.sort(key=lambda g: g.timestamp)

		result = cls(
			name      = '+'.join(names),
			gulps     = gulps,
			author    = '+'.join(names),
			role      = '',
			is_zipped = True
		)
		return result

	# Return gulps since timestamp
	# ----------------------------------------------------------------------
	def since(self, timestamp):
		result = self._gulps_to_stream(
			[g for g in self.gulps if g.timestamp > timestamp]
		)
		return result

	# Return last n gulps
	# ----------------------------------------------------------------------
	def last(self, n=1):
		gulps  = self.gulps[-n:] if n > 0 else self.gulps
		result = self._gulps_to_stream(gulps)

		return result

	# Return last gulp
	# ----------------------------------------------------------------------
	def last_gulp(self):
		result = self.gulps[-1] if self.gulps else None
		return result

	# Return substream since last author appearance
	# ----------------------------------------------------------------------
	def since_last_author(self, author, inclusive=True):
		gulps = self.gulps or []
		idx = next(
			(i for i in range(len(gulps)-1, -1, -1) if gulps[i].author == author),
			None
		)

		if idx is None:
			result = self._gulps_to_stream([])
		else:
			result = self._gulps_to_stream(
				gulps[idx:] if inclusive else gulps[idx+1:]
			)

		return result

	# Write new gulps
	# ----------------------------------------------------------------------
	def write(self, values):
		if self.is_zipped:
			raise RuntimeError(f'🛑 Cannot write to zipped stream `{self.name}`')

		if not isinstance(self.gulps, list):
			self.gulps = []

		values = [values] if isinstance(values, str) else values
		self.gulps = self.gulps or []

		for value in values:
			if not isinstance(value, str):
				raise ValueError(f'🛑 Cannot write non–string to stream `{self.name}`')

			self.gulps.append(Gulp(
				value  = str(value),
				author = self.author
			))

			self.save()
			self.log(value)

		return self

	# Read gulps with filters
	# ----------------------------------------------------------------------
	def read(self, limit=None, since=None):
		stream = self

		if since is not None:
			stream = stream.since(since)

		if limit is not None:
			stream = stream.last(int(limit))

		result = stream.gulps
		return result

	# Write log file
	# ----------------------------------------------------------------------
	def log(self, s):
		log_path = os.path.join(ww.config.LOGS_DIR, f'{self.name}.log')

		with open(log_path, 'a') as f:
			f.write(f'{s.strip()}\n')

	# Convert to list of values
	# ----------------------------------------------------------------------
	def to_list(self):
		result = [g.value for g in self.gulps]
		return result

	# Convert to prompt
	# ----------------------------------------------------------------------
	def to_prompt(self):
		result = '\n'.join([g.to_prompt() for g in self.gulps])
		return result
