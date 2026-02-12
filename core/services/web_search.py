# ======================================================================
# WebSearch
# ======================================================================

import ww


class WebSearch(ww.Service):

	def initialize(self):
		self.rag     = ww.services.Rag
		self.google  = ww.services.Google
		self.website = ww.services.Website

	# ----------------------------------------------------------------------
	def get_domain_id(self, query):
		return f'web_{abs(hash(query))}'

	# ----------------------------------------------------------------------
	async def search(self, query, k_results=5, k_chunks=10):

		domain_key = self.get_domain_id(query)

		# 1. Ingest only if domain does not exist
		if not self.rag.has_domain(domain_key):

			docs = self.google.search(
				query      = query,
				time_range = (None, None),
				top_k      = k_results
			)

			docs = await self.website.load(docs)

			for doc in docs:
				if doc and doc.text:
					self.rag.add_document(
						domain_id    = domain_key,
						document_key = doc.name,
						text         = doc.text,
						mtime        = doc.mtime,
						description  = doc.title,
						temporary    = True
					)

		# 2. Search
		return self.rag.search(
			domain_id_or_key = domain_key,
			query            = query,
			top_k            = k_chunks
		)
