# ======================================================================
# Expertise wrapper around Rag for folder-based knowledge.
# ======================================================================

import os

from wordwield.core.base.service import Service
from wordwield.core.fs           import Directory, File


class ExpertiseService(Service):

	# ------------------------------------------------------------------
	def initialize(self):
		self.rag          = self.ww.services.RagService
		self.domain_key   = 'expertise'
		self.domain_id    = self.rag.set_domain(self.domain_key)
		self.folder       = self.ww.config.EXPERTISE_DIR
		self.readable_ext = self.ww.config.EXPERTISE_FILE_EXT

		self.sync()

	# ------------------------------------------------------------------
	def sync(self):
		fs_docs     = Directory(self.folder).list_files(extensions=self.readable_ext)
		domain_docs = self.rag.get_documents(self.domain_id)

		# Remove if deleted in fs, fs has newer version
		for domain_doc in domain_docs:
			if domain_doc.key not in fs_docs or domain_doc.mtime < fs_docs[domain_doc.key]:
				self.rag.unset_document(self.domain_id, domain_doc.id)

		# Index missing/removed files
		domain_docs      = self.rag.get_documents(self.domain_id)
		domain_docs_keys = {d.key for d in domain_docs}

		for key in fs_docs:
			if key not in domain_docs_keys:
				self.ww.log_info(f'Indexing `{key}`')
				text  = File(key).read()
				mtime = int(fs_docs[key])
				self.rag.set_document(
					domain_id    = self.domain_id,
					document_key = key,
					text         = text,
					mtime        = mtime
				)

	# ------------------------------------------------------------------
	def search(self, query, top_k, max_steps):
		return self.rag.search(
			domain_id = self.domain_id,
			query     = query,
			top_k     = top_k,
			max_steps = max_steps
		)
