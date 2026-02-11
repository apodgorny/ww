import o


class SemanticDomain(o.Schema):
	description = o.F(str,  default='')
	temporary   = o.F(bool, default=True)
	created     = o.F(int)

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Get all domain documents
	# ----------------------------------------------------------------------
	def get_documents(self):
		return o.T.SemanticDocument.get_all(domain=self)

	# Get document by key or id for given domain
	# ----------------------------------------------------------------------
	def get_document(self, id_or_key):
		if isinstance(id_or_key, str):
			return o.T.SemanticDocument.get_one(domain=self, key=id_or_key)
		return o.T.SemanticDocument.get_one(domain=self, id=id_or_key)

	# Add document to domain
	# ----------------------------------------------------------------------
	def add_document(self, key, *, mtime, description=None):
		doc = o.T.SemanticDocument(
			key         = key,
			domain      = self,
			mtime       = mtime,
			description = description,
		).save()
		return doc.id

	# Remove document from domain
	# ----------------------------------------------------------------------
	def remove_document(self, document_id):
		doc = o.T.SemanticDocument.load(document_id)
		if doc.domain.id is self.id:
			return doc.remove()
		return False

	# Delete with cascade
	# ----------------------------------------------------------------------
	def remove(self):
		for doc in self.get_documents():
			doc.remove()

		self.delete()
		return True
