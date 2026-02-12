# ======================================================================
# Google — web discovery (with DB cache)
# ======================================================================

import time
import requests

import ww, o


class Google(ww.Service):

	# Initialize service
	# ----------------------------------------------------------------------
	def initialize(self):
		self.google_api_key   = ww.Conf.GOOGLE_API_KEY
		self.search_engine_id = ww.Conf.GOOGLE_SEARCH_ENGINE_ID
		self.timeout          = 20

	# ======================================================================
	# PRIVATE METHODS
	# ======================================================================

	# Extract publication timestamp from Google item
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
				point = o.T.TimePoint.from_iso(tag.get(key))
				if point is not None:
					result = point.timestamp
					break
			if result is not None:
				break

		return result


	# Perform raw Google API request
	# ----------------------------------------------------------------------
	def _request(self, query, top_k):
		if not self.google_api_key or not self.search_engine_id:
			raise RuntimeError('Google search credentials are not configured.')

		url = 'https://www.googleapis.com/customsearch/v1'

		params = dict(
			key = self.google_api_key,
			cx  = self.search_engine_id,
			q   = query,
			num = min(top_k, 10)
		)

		response = requests.get(
			url,
			params  = params,
			timeout = self.timeout
		)

		response.raise_for_status()

		return response.json()


	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Perform Google search with DB caching
	# ----------------------------------------------------------------------
	def search(self, query, time_range=None, top_k=5):

		results = []

		# --------------------------------------------------------------
		# 1. Try cache
		# --------------------------------------------------------------
		cache = o.T.WebQuery.get_one(
			query = query,
			top_k = top_k
		)

		data = None

		if cache is not None:
			data = cache.results
			self.print(f'Loaded `{query}` from cache')
		else:
			self.print(f'Searching `{query}` via Google')
			data = self._request(query, top_k)

			o.T.WebQuery(
				query   = query,
				top_k   = top_k,
				results = data,
				created = int(time.time())
			).save()


		# --------------------------------------------------------------
		# 2. Filter and normalize
		# --------------------------------------------------------------
		items = data.get('items', []) if data else []

		from_ts, to_ts = time_range if time_range else (None, None)

		for item in items:

			link      = item.get('link')
			published = self._publish_date(item)

			too_old    = from_ts and published and published < from_ts
			too_recent = to_ts   and published and published > to_ts

			is_valid = bool(link) and not too_old and not too_recent

			if is_valid:
				results.append(o.T.WebPage(
					name    = link,
					title   = item.get('title'),
					snippet = item.get('snippet'),
					mtime   = published,
					source  = 'google'
				))

		self.print(f'Found {len(results)} results')

		return results
