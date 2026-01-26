# ======================================================================
# Web page loading and text extraction service.
# ======================================================================

import asyncio
from time import time

import requests
import trafilatura

from tqdm import tqdm

from wordwield.core.base.service import Service


class WebsiteService(Service):
	timeout    = 20
	user_agent = 'WordWield-Website/1.0'

	# Initialize
	# ----------------------------------------------------------------------
	def initialize(self):
		# Explicitly set defaults for clarity; class attributes provide safe
		# fallbacks when the service is used before initialization completes.
		self.timeout    = 20
		self.user_agent = 'WordWield-Website/1.0'

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Do the actual request
	# ----------------------------------------------------------------------
	async def request(self, url):
		try:
			response = requests.get(
				url,
				timeout = self.timeout,
				headers = {'User-Agent': self.user_agent}
			)
			response.raise_for_status()
		except requests.exceptions.HTTPError:
			return None
		return response.text  # raw html

	# Extract readable text from HTML
	# ----------------------------------------------------------------------
	def extract_text(self, html):
		text = None
		if html:
			text = trafilatura.extract(
				html,
				include_comments = False,
				include_tables   = False
			)
		return text
	
	# Load html from web, extract text, update doc/docs object/s, cache, return
	# ----------------------------------------------------------------------
	async def load(self, doc):
		if doc:
			if isinstance(doc, list):                                         # Load many
				doc = await asyncio.gather(*[self.load(d) for d in doc])
			elif isinstance(doc, self.ww.schemas.DocSchema):                  # Load one
				cache_doc = self.ww.schemas.DocSchema.load(doc.name)
				if cache_doc:
					print('Loading from cache')
					doc = cache_doc
				else:
					print('Loading from web')
					html = await self.request(doc.name)                        # Url is mandatory field in schema
					text = self.extract_text(html)

					doc = self.ww.schemas.DocSchema.put(
						name       = doc.name,
						title      = doc.title,
						snippet    = doc.snippet,
						mtime      = doc.mtime,
						source     = doc.source,
						html       = html,
						text       = text,
						fetched_at = int(time())
					)
		return doc
