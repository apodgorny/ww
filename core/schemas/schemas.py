import os
from time import time

from typing          import Optional
from wordwield.core.o import O
from wordwield       import ww


class GulpSchema(O):
	timestamp : int = O.Field(description='Time of occurrence', llm=False, semantic=True)
	value     : str = O.Field(description='Output value',       llm=True,  semantic=True)
	author    : str = O.Field(description='Gulp author',        llm=False)

	def __str__(self)  : return f'Gulp [{self.timestamp}] {self.author}: "{self.value}"'
	def __repr__(self) : return str(self)
	
	@classmethod
	def on_create(cls, data):
		if 'timestamp' not in data or data['timestamp'] is None:
			data['timestamp'] = int(time() * 1000)
		return data

	def to_prompt(self):
		return f'[{self.author}]: "{self.value}"'

class StreamSchema(O):
	name      : str              = O.Field(semantic=True, description='Stream name', llm=False)
	role      : str              = O.Field(description='Stream role', llm=False)
	gulps     : list[GulpSchema] = O.Field(semantic=True, description='Ordered sequence of output values', default_factory=list, llm=False)
	author    : str              = O.Field(description='Name(s) of agent(s) who owns this stream')
	is_zipped : bool             = False

	# Magic
	############################################################################################

	def __len__(self):
		return len(self.gulps or [])

	# Private
	############################################################################################

	def _gulps_to_stream(self, gulps):
		return StreamSchema(
			name   = self.name,
			role   = self.role,
			gulps  = gulps,
			author = self.author
		)
	
	# Public
	############################################################################################

	@classmethod
	def zip(cls, *names):
		gulps   = []
		for name in names:
			if stream := cls.load(name):
				for g in stream.gulps or []:
					gulps.append(g.clone())
		gulps.sort(key=lambda g: g.timestamp)

		return cls(
			name      = '+'.join(names),
			gulps     = gulps,
			author    = '+'.join(names),
			role      = '',
			is_zipped = True
		)

	def since(self, timestamp: int) -> 'StreamSchema':
		return self._gulps_to_stream([g for g in self.gulps if g.timestamp > timestamp])

	def last(self, n: int = 1) -> 'StreamSchema':
		return self._gulps_to_stream(self.gulps[-n:] if n > 0 else self.gulps)
	
	def last_gulp(self):
		return self.gulps[-1] if self.gulps else None
	
	def since_last_author(self, author: str, inclusive: bool = True) -> 'StreamSchema':
		'''
		Возвращает substream, начиная с последнего появления указанного автора.
		Если inclusive=True — с этим gulp включительно, иначе — только после.
		Если автор не найден — возвращает пустой substream.
		'''
		gulps = self.gulps or []
		idx   = next((i for i in range(len(gulps)-1, -1, -1) if gulps[i].author == author), None)
		if idx is None:
			return self._gulps_to_stream([])
		return self._gulps_to_stream(gulps[idx:] if inclusive else gulps[idx+1:])

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
			
			self.gulps.append(GulpSchema(
				value  = str(value),
				author = self.author
			))
			self.save()
			self.log(value)

		return self

	def read(self, limit=None, since=None):
		stream = self
		if since is not None : stream = stream.since(since)
		if limit is not None : stream = stream.last(int(limit))
		return stream.gulps

	def log(self, s):
		log_path = os.path.join(ww.config.LOGS_DIR, f'{self.name}.log')
		with open(log_path, 'a') as f:
			f.write(f'{s.strip()}\n')

	def to_list(self):
		return [g.value for g in self.gulps]

	def to_prompt(self):
		return '\n'.join([g.to_prompt() for g in self.gulps])
