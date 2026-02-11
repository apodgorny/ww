# ======================================================================
# Document registry (id → human key) within domain.
# ======================================================================

import time

from sqlalchemy import (
	ForeignKey,
	Column,
	DateTime,
	Integer,
	Text,
	CheckConstraint,
	UniqueConstraint,
	Boolean
)
from sqlalchemy.orm import relationship

import ww


class SemanticDocument(ww.base.Record):
	__tablename__ = 'semantic_document'

	# Foreign
	domain_id = Column(
		Integer,
		ForeignKey('semantic_domain.id', ondelete='CASCADE'),
		nullable=False
	)

	# Local
	id        = Column(Integer,  primary_key=True)    # 16-bit document id (part of Sid)
	key       = Column(Text,     nullable=False)      # path / url / slug
	meta      = Column(Text,     nullable=True)       # optional json/text
	mtime     = Column(Integer,  nullable=False)      # external modification time
	created   = Column(Integer,  nullable=False)      # creation time

	# Constraints
	# ----------------------------------------------------------------------
	__table_args__ = (
		CheckConstraint(
			'id >= 0 AND id < 65536',
			name = 'ck_semantic_document_id_16bit'
		),
		UniqueConstraint(
			'id', 'domain_id',
			name = 'uq_semantic_document_id_domain'
		),
		UniqueConstraint(
			'key', 'domain_id',
			name = 'uq_semantic_document_key_domain'
		),
	)

	# Relationships
	# ----------------------------------------------------------------------
	# domain = relationship(
	# 	'SemanticDomain',
	# 	back_populates = 'documents',
	# )

	# atoms = relationship(
	# 	'SemanticAtom',
	# 	back_populates  = 'document',
	# 	cascade         = 'all, delete-orphan',
	# 	passive_deletes = True,
	# )

	def __repr__(self):
		return f'<SemanticDocument id={self.id} domain_id={self.domain_id} key={self.key} >'

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Get document by domain and id
	# ----------------------------------------------------------------------
	@classmethod
	def get(
		cls,
		domain_id   : int,
		document_id : int
	):
		return cls.session.query(cls).filter_by(
			domain_id = domain_id,
			id        = document_id
		).first()

	# Get document by domain and key
	# ----------------------------------------------------------------------
	@classmethod
	def get_by_key(
		cls,
		domain_id    : int,
		document_key : str
	):
		return cls.session.query(cls).filter_by(
			domain_id = domain_id,
			key       = document_key
		).first()

	# Create or update document
	# ----------------------------------------------------------------------
	@classmethod
	def set(
		cls,
		domain_id : int,
		key       : str,
		*,
		mtime     : int,
		meta      : str | None = None,
		id        : int | None = None,
	) -> int:
		row = cls.get_by_key(domain_id, key)

		if id is None or row is not None:
			last = (
				cls.session
					.query(cls.id)
					.filter_by(domain_id=domain_id)
					.order_by(cls.id.desc())
					.first()
			)
			id = int(last[0]) + 1 if last else 0

		if id < 0 or id > 0xFFFF:
			raise ValueError('Document id must fit in 16 bits')

		row = cls(
			id        = id,
			domain_id = domain_id,
			key       = key,
			meta      = meta,
			mtime     = mtime,
			created   = int(time.time())
		)

		row = cls.session.merge(row)
		cls.session.flush()

		return int(row.id)

	# Remove document and all its atoms
	# ----------------------------------------------------------------------
	@classmethod
	def unset(
		cls,
		domain_id   : int,
		document_id : int | str
	) -> bool:
		row = cls.get(domain_id, document_id)

		if row is not None:
			cls.session.delete(row)
			cls.session.flush()
			ok = True
		else:
			ok = False

		return ok

	# ======================================================================
	# ATOM MANAGEMENT
	# ======================================================================

	# Add one atom to this document
	# ----------------------------------------------------------------------
	def set_atoms(self, texts, vectors):
		vector_ids = []

		for item_id in range(len(texts)):
			atom_id = Sid(
				domain_id   = self.domain_id,
				document_id = self.id,
				item_id     = item_id
			).id

			SemanticAtom.set(
				sid    = atom_id,
				text   = texts[item_id],
				vector = vectors[item_id],
			)

			vector_ids.append(atom_id)

		SemanticAtom.session.flush()
		return vector_ids


# Relations
# --------------------------------------------------------------------------------
ww.db.Relations.add(
	ww.db.SemanticDocument, 'domain',
	ww.db.SemanticDomain,
	back_populates = 'documents'
)

ww.db.Relations.add(
	ww.db.SemanticDocument, 'atoms',
	ww.db.SemanticAtom,
	back_populates  = 'document',
	cascade         = 'all, delete-orphan',
	passive_deletes = True,
)