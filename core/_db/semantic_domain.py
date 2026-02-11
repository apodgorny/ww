# ======================================================================
# Domain registry (human → numeric).
# ======================================================================

import time

from sqlalchemy import (
	Column,
	DateTime,
	Integer,
	Text,
	CheckConstraint,
	Boolean
)
from sqlalchemy.orm import relationship

import ww



class SemanticDomain(ww.base.Record):
	__tablename__ = 'semantic_domain'

	id        = Column(Integer,  primary_key=True)             # 16-bit domain id
	key       = Column(Text,     nullable=False, unique=True)  # domain name
	meta      = Column(Text,     nullable=True)                # optional json/text
	created   = Column(Integer,  nullable=False)               # domain creation time
	temporary = Column(Boolean,  default=True, nullable=False) # temporary domain flag

	# Constraints
	# ----------------------------------------------------------------------
	__table_args__ = (
		CheckConstraint(
			'id >= 0 AND id < 65536',
			name='ck_semantic_domain_id_16bit'
		),
	)

	# Relationships
	# ----------------------------------------------------------------------
	# documents = relationship(
	# 	'SemanticDocument',
	# 	back_populates  = 'domain',
	# 	cascade         = 'all, delete-orphan',
	# 	passive_deletes = True,
	# )

	def __repr__(self):
		return f'<SemanticDomain id={self.id} key={self.key}>'

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Get domain by id
	# ----------------------------------------------------------------------
	@classmethod
	def get(cls, domain_id: int | str):
		return cls.session.query(cls).filter_by(id=domain_id).first()

	# Get domain by key
	# ----------------------------------------------------------------------
	@classmethod
	def get_by_key(cls, domain_key: int | str):
		return cls.session.query(cls).filter_by(key=domain_key).first()

	# Create or return existing domain id
	# ----------------------------------------------------------------------
	@classmethod
	def set(
		cls,
		key       : str,
		*,
		id        : int | None = None,
		meta      : str | None = None,
		temporary : bool       = False
	) -> int:
		row = cls.get_by_key(key)

		if row is None:
			if id is None:
				max_id = cls.session.query(cls.id).order_by(cls.id.desc()).first()
				id = int(max_id[0]) + 1 if max_id else 0

			if id < 0 or id > 0xFFFF:
				raise ValueError('Domain id must fit in 16 bits')

			row = cls(
				id        = id,
				key       = key,
				meta      = meta,
				temporary = temporary,
				created   = int(time.time())
			)

			ww.services.Db.add(row)
			ww.services.Db.flush()

		return int(row.id)

	# List all domains
	# ----------------------------------------------------------------------
	@classmethod
	def get_all(cls, temporary=None):
		query = ww.services.Db.query(cls)
		if temporary is not None:
			query = query.filter_by(temporary=temporary)
		return query.all()

	# Remove domain with all documents and atoms
	# ----------------------------------------------------------------------
	@classmethod
	def unset(cls, domain_id: int | str) -> bool:
		row = cls.get(domain_id)

		if row is not None:
			ww.services.Db.delete(row)
			ww.services.Db.flush()
			return True

		return False

	# ======================================================================
	# DOCUMENT MANAGEMENT
	# ======================================================================

	# Get all documents in this domain
	# ----------------------------------------------------------------------
	def get_documents(self):
		return list(self.documents)

	# Create or update document in this domain
	# ----------------------------------------------------------------------
	def set_document(
		self,
		key  : str,
		*,
		mtime: int,
		meta : str | None = None
	) -> int:
		document_id = SemanticDocument.set(
			domain_id = self.id,
			key       = key,
			mtime     = mtime,
			meta      = meta
		)

		return document_id

	# Remove document from this domain
	# ----------------------------------------------------------------------
	def unset_document(self, document_id: str) -> bool:
		removed = SemanticDocument.unset(
			domain_id   = self.id,
			document_id = document_id
		)

		return removed

# Relations
# --------------------------------------------------------------------------------
ww.db.Relations.add(
	ww.db.SemanticDomain, 'documents',
	ww.db.SemanticDocument,
	back_populates  = 'domain',
	cascade         = 'all, delete-orphan',
	passive_deletes = True,
)