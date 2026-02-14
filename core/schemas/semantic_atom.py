import ww, o, yo

o.T.SemanticDocument


class SemanticAtom(o.Schema):
	document = o.F( o.T.SemanticDocument, 'Document containing atom' )
	item_id  = o.F( int,                  'Id of item in database'   )
	text     = o.F( str,                  'Actual text of atom'      )
	vector   = o.F( yo.T.Tensor,          'Vectorized text'          )
	created  = o.F( int,                  'Time created'             )

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
