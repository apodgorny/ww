from time import time

from typing           import Optional
from urllib.parse     import urlparse

from wordwield.core.o import O


class DocSchema(O):
	name       : str
	title      : Optional[str] = O.Field(description='Document title', llm=True, semantic=True, default='')
	snippet    : Optional[str] = O.Field(description='Search snippet or preview', llm=True, semantic=True, default=None)
	text       : Optional[str] = O.Field(description='Extracted plain text', llm=True, semantic=True, default='')
	html       : Optional[str] = O.Field(description='Raw HTML content', llm=False, default='')
	mtime      : int = O.Field(description='Source modification time (unix seconds)', llm=False)
	fetched_at : int = O.Field(description='Fetch time (unix seconds)', llm=False)
	source     : str = O.Field(description='Origin system (google/web/other)', llm=False)

	def __str__(self):
		name = self.name
		if 'http' in self.name:
			name = urlparse(self.name)
		return f'Doc [{name.scheme}://{name.netloc}] `{self.title}` ({len(self.html)}/{len(self.text)} chars)'

	def __repr__(self):
		return str(self)

	@classmethod
	def on_create(cls, data):
		if data is None:
			return data

		if isinstance(data, dict):
			if not data.get('key') and data.get('url'):
				data['key'] = data['url']
			if data.get('fetched_at') is None:
				data['fetched_at'] = int(time())
		return data
