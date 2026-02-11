# ======================================================================
# Expertise wrapper around Rag for folder-based knowledge.
# ======================================================================

import ww, o, yo


class Expertise(ww.Service):

	# ------------------------------------------------------------------
	def initialize(self):
		self.sync(ww.Conf.EXPERTISE)

	# ------------------------------------------------------------------
	def sync(self, dir):
		for entry in dir:
			if entry.is_directory:
				fs_keys = set()
				domain  = ww.services.Rag.add_domain(entry.name, description=f'Expertise domain {entry.name}')

				for fs_doc in entry:
					print('FS_DOC:', fs_doc.path, fs_doc.ext)
					if fs_doc.ext in ['md', 'txt']:
						fs_keys.add(fs_doc.path)

						# Remove if fs has newer version
						# - - - - - - - - - - - - - - - - - - - -
						domain_doc = domain.get_document(fs_doc.path)
						if domain_doc is not None:
							if domain_doc.mtime < fs_doc.mtime:
								ww.services.rag.remove_document(domain.id, domain_doc.id)

						# Index missing files
						# - - - - - - - - - - - - - - - - - - - -
						if domain.get_document(fs_doc.path) is None:
							self.print(f'Indexing `{fs_doc.path}`')
							ww.services.rag.add_document(
								domain_id    = domain.id,
								document_key = fs_doc.path,
								text         = fs_doc.load(),
								mtime        = fs_doc.mtime
							)

				# Remove documents missing from filesystem
				# - - - - - - - - - - - - - - - - - - - -
				for domain_doc in domain.get_documents():
					if domain_doc.key not in fs_keys:
						self.print(f'Removing `{domain_doc.key}` (missing in fs)')
						ww.services.rag.remove_document(domain.id, domain_doc.id)

	# Search within given domain
	# ------------------------------------------------------------------
	def search(self, domain_key, query, top_k):
		print('Searching', domain_key)
		print(o.T.SemanticAtom.report())
		print(o.T.SemanticDocument.report())
		print(o.T.SemanticDomain.report())
		domain = o.T.SemanticDomain.load(domain_key)
		print('Loaded domain', domain)
		if domain is None:
			raise ValueError(f'Domain `{domain_key}` does not exist.')

		return ww.services.Rag.search(domain.id, query, top_k)
