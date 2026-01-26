# ======================================================================
# Google search service (discovery only).
# ======================================================================

import json

import requests

from wordwield.core.base.service import Service


class GoogleService(Service):

	# Service initialization
	# ----------------------------------------------------------------------
	def initialize(self):
		self.google_api_key   = self.ww.env.GOOGLE_API_KEY
		self.search_engine_id = self.ww.env.GOOGLE_SEARCH_ENGINE_ID
		self.timeout          = 20

	# ======================================================================
	# PRIVATE METHODS
	# ======================================================================

	# Extract publication date from search item
	# ----------------------------------------------------------------------
	def _publish_date(self, item):
		result = None
		meta   = item.get('pagemap', {}).get('metatags', [])

		for tag in meta:
			for key in (
				'article:published_time',
				'article:modified_time',
				'og:updated_time',
				'datepublished',
				'pubdate'
			):
				point = self.ww.schemas.TimePointSchema.from_iso(tag.get(key))
				if point is not None:
					result = point.timestamp
					break
			if result is not None:
				break
		return result

	# Query Google search API.
	# ----------------------------------------------------------------------
	def _search(self, query, time_range, top_k):
		# cache_key = f'{query} {time_range} {top_k}'
		# print(cache_key)
		# web_search = self.ww.schemas.WebSearchSchema.load(cache_key)
		# if web_search:

		if not self.google_api_key or not self.search_engine_id:
			raise RuntimeError('Google search credentials are not configured.')

		google_api_url = 'https://www.googleapis.com/customsearch/v1'
		from_ts, to_ts = time_range                                     # Unix timestamps
		from_point     = self.ww.schemas.TimePointSchema.create(from_ts) if from_ts is not None else None
		to_point       = self.ww.schemas.TimePointSchema.create(to_ts) if to_ts is not None else None

		params = {
			'key' : self.google_api_key,
			'cx'  : self.search_engine_id,
			'q'   : query,
			'num' : min(top_k, 10)
		}

		self.log(f'Searching `{query}` ...')
		response = requests.get(
			google_api_url,
			params  = params,
			timeout = self.timeout
		)

		response.raise_for_status()

		data    = response.json()
		items   = data.get('items', [])
		results = []

		for item in items:
			print(item.get('link'), self._publish_date(item))
			link       = item.get('link')
			published  = self._publish_date(item)
			too_old    = from_point and published and published < from_point.timestamp
			too_recent = to_point   and published and published > to_point.timestamp

			is_valid = bool(link)

			if too_old or too_recent:
				is_valid = False

			if is_valid:
				results.append(self.ww.schemas.DocSchema(
					name    = link,
					title   = item.get('title'),
					snippet = item.get('snippet'),
					mtime   = published,
					source  = 'google'
				))
			exit(1)
		return results

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Perform a Google search
	# ----------------------------------------------------------------------
	def search(self, query, time_range, top_k):
		results = self._search(query=query, time_range=time_range, top_k=top_k)
		self.log(f'Found {len(results)} results')
		return results
