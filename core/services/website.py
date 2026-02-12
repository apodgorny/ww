# ======================================================================
# Website — load HTML and extract readable text.
# ======================================================================

import aiohttp
import trafilatura

import ww


class Website(ww.Service):

	timeout    = 20
	user_agent = 'WordWield-Website/1.0'


	# ------------------------------------------------------------------
	def initialize(self):
		self.timeout    = Website.timeout
		self.user_agent = Website.user_agent


	# ------------------------------------------------------------------
	async def request(self, url):
		headers = {'User-Agent': self.user_agent}
		timeout = aiohttp.ClientTimeout(total=self.timeout)

		text = None

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
	async def load(self, url):
		html = await self.request(url)
		text = self.extract_text(html)
		return text
