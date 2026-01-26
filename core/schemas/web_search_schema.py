from time import time

from typing           import Optional
from urllib.parse     import urlparse

from wordwield.core.o import O


class WebSearchSchema(O):
	name  : str
	query : str
	urls  : list[str]

	def __str__(self):
		name = self.name
		if 'http' in self.name:
			name = urlparse(self.name)
		return f'WebSearch `{self.query}`'

	def __repr__(self):
		return str(self)