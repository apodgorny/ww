# ======================================================================
# WebPage — crawled or indexed web document.
# ======================================================================

from time         import time
from urllib.parse import urlparse

import o


class WebPage(o.Schema):

	name       = o.F(str)
	title      = o.F(str, default='')
	snippet    = o.F(str, default=None)
	text       = o.F(str, default='')
	html       = o.F(str, default='')
	mtime      = o.F(int)
	fetched_at = o.F(int)
	source     = o.F(str)


	# ----------------------------------------------------------------------
	def __str__(self):

		name   = self.name
		scheme = ''
		host   = ''

		if isinstance(name, str) and name.startswith('http'):

			parsed = urlparse(name)
			scheme = parsed.scheme
			host   = parsed.netloc

		result = f'WebPage [{scheme}://{host}] `{self.title}` ({len(self.html)}/{len(self.text)} chars)'
		return result


	# ----------------------------------------------------------------------
	def __repr__(self):

		result = str(self)
		return result


	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Normalize input before creation
	# ----------------------------------------------------------------------
	@classmethod
	def on_create(cls, data):

		result = data

		if isinstance(result, dict):

			if result.get('fetched_at') is None:
				result['fetched_at'] = int(time())

		return result
