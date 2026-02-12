import ww, o, yo

o.T.SemanticDocument


class SemanticAtom(o.Schema):
	document = o.F(o.T.SemanticDocument)
	item_id  = o.F(int)
	text     = o.F(str)
	vector   = o.F(yo.T.Tensor)
	created  = o.F(int)

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Remove atom
	# ----------------------------------------------------------------------
	@o.dual_method
	def remove(cls, self, atom_id=None):
		if self:
			return self.delete()
		return cls.delete(atom_id)
