# ======================================================================
# WebSite — load HTML and extract readable text.
# ======================================================================

import aiohttp
import trafilatura

import ww, o


class WebSite(ww.Service):

	timeout    = 20
	user_agent = 'WordWield-WebSite/1.0'

	# ------------------------------------------------------------------
	def initialize(self):
		self.timeout    = WebSite.timeout
		self.user_agent = WebSite.user_agent

	# ------------------------------------------------------------------
	async def request(self, url):
		headers = {'User-Agent': self.user_agent}
		timeout = aiohttp.ClientTimeout(total=self.timeout)
		text    = None

		async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
			async with session.get(url) as resp:
				if resp.status >= 400:
					resp.raise_for_status()
				text = await resp.text(errors='ignore')

		return text

	# ------------------------------------------------------------------
	def extract_text(self, html):
		text = None

		if html:
			text = trafilatura.extract(
				html,
				include_comments = False,
				include_tables   = False
			)

		return text

	# ------------------------------------------------------------------
	async def load(self, docs):
		result = []

		for doc in docs:
			html = await self.request(doc.name)
			text = self.extract_text(html)

			doc.html = html
			doc.text = text

			result.append(doc)

		return result

