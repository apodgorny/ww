# ======================================================================
# WebQuery — cached Google search result
# ======================================================================

import o


class WebQuery(o.Schema):

	query   = o.F(str)
	top_k   = o.F(int)
	results = o.F(dict)
	created = o.F(int)

	def on_save(self):
		self.print(f'Cached Google query `{self.query}`')