import o


class SemanticDocument(o.Schema):
	domain      = o.F(o.T.SemanticDomain)
	description = o.F(str, default=None)
	mtime       = o.F(int)
	created     = o.F(int)

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Get all document atoms
	# ----------------------------------------------------------------------
	def get_atoms(self):
		return o.T.SemanticAtom.get_all(document=self)

	# Add atoms to document
	# ----------------------------------------------------------------------
	def add_atoms(self, texts, vectors):
		ids = []

		for item_id in range(len(texts)):
			atom = o.T.SemanticAtom(
				document = self,
				item_id  = item_id,
				text     = texts[item_id],
				vector   = vectors[item_id],
			).save()
			ids.append(atom.id)

		return ids

	# Delete with cascade
	# ----------------------------------------------------------------------
	def remove(self):
		for atom in self.get_atoms():
			atom.remove()

		self.delete()
		return True
