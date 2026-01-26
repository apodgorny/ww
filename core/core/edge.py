from typing import Any

from sqlalchemy import and_

from wordwield.core.db import EdgeRecord


class Edge:
	def __init__(self, session):
		self.session = session
		self.model   = EdgeRecord

	# Private methods
	############################################################################

	def _get_filter(self, id1, id2, rel1, rel2):
		return and_(
			self.model.id1  == id1,
			self.model.id2  == id2,
			self.model.rel1 == rel1,
			self.model.rel2 == rel2,
		)

	# Public methods
	############################################################################

	def set(self, id1, id2, type1, type2, rel1, rel2, key1='', key2=''):
		key1 = str(key1) if key1 is not None else ''
		key2 = str(key2) if key2 is not None else ''
		rel2 = str(rel2) if rel2 is not None else ''
		# остальные параметры, если могут быть None, тоже!
		exists = self.session.query(self.model).filter_by(
			id1=id1, id2=id2, type1=type1, type2=type2,
			rel1=rel1, rel2=rel2, key1=key1, key2=key2
		).first()
		if not exists:
			self.session.add(self.model(
				id1=id1, id2=id2, type1=type1, type2=type2,
				rel1=rel1, rel2=rel2, key1=key1, key2=key2
			))

	def unset(self, id1, id2, rel1, rel2):
		self.session.query(self.model).filter(
			self._get_filter(id1, id2, rel1, rel2)
		).delete()

	def get(self, obj: Any, rel: str = None):
		query = self.session.query(EdgeRecord).filter(
			(EdgeRecord.id1 == obj.id) | (EdgeRecord.id2 == obj.id)
		)
		if rel is not None:
			query = query.filter(
				(EdgeRecord.rel1 == rel) | (EdgeRecord.rel2 == rel)
			)
		return query.all()
