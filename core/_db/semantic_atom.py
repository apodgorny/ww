# ======================================================================
# Semantic atom sql model and helpers.
# ======================================================================

from datetime import datetime

import torch
import numpy as np

from sqlalchemy     import ForeignKey, Column, DateTime, Integer, LargeBinary, Text
from sqlalchemy.orm import relationship

import ww


# ======================================================================
# PRIVATE METHODS
# ======================================================================

# Serialize vector to binary blob
# ----------------------------------------------------------------------
def vector_serialize(vector):
	if vector is None:
		return None
	if isinstance(vector, torch.Tensor):
		arr = vector.detach().to(torch.float32).cpu().numpy()
	elif isinstance(vector, np.ndarray):
		arr = vector.astype(np.float32)
	else:
		arr = np.asarray(vector, dtype=np.float32)
	return arr.tobytes()

# Deserialize vector from binary blob
# ----------------------------------------------------------------------
def vector_deserialize(blob):
	if blob is None:
		return None
	if isinstance(blob, torch.Tensor):
		return blob
	if isinstance(blob, np.ndarray):
		return torch.from_numpy(blob.astype(np.float32))
	if isinstance(blob, (bytes, bytearray, memoryview)):
		arr = np.frombuffer(blob, dtype=np.float32)
		return torch.from_numpy(arr)
	return torch.as_tensor(blob, dtype=torch.float32)


# ======================================================================
# MODEL
# ======================================================================

class SemanticAtom(ww.base.Record):
	__tablename__ = 'semantic_atom'

	# Foreign
	document_id = Column(
		Integer,
		ForeignKey('semantic_document.id', ondelete='CASCADE'),
		nullable = False
	)

	# Local
	id      = Column(Integer,     primary_key=True)   # Global semantic id (Sid)
	text    = Column(Text,        nullable=False)
	vector  = Column(LargeBinary, nullable=True)
	created = Column(DateTime,    default=datetime.utcnow)

	# Relationships
	# ----------------------------------------------------------------------
	# document = relationship(
	# 	'SemanticDocument',
	# 	back_populates='atoms',
	# )

	# ----------------------------------------------------------------------
	def __repr__(self):
		return f'<SemanticAtom id={self.id} document_id={self.document_id}>'

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	def save(self):
		self.session.add(self)

	# Get atom by semantic id
	# ----------------------------------------------------------------------
	@classmethod
	def get(cls, sid: Sid | int | None = None):
		query  = cls.session.query(cls)
		result = {}

		if sid is not None:
			v = sid if isinstance(sid, Sid) else Sid(id=sid)
			query = query.filter(cls.id == v.id)

		for row in query.all():
			result[int(row.id)] = {
				'text'   : row.text,
				'vector' : vector_deserialize(row.vector)
			}

		return result

	# Remove atom by semantic id
	# ----------------------------------------------------------------------
	@classmethod
	def unset(cls, sid: Sid | int | None = None):
		removed = False

		if sid is not None:
			v = sid if isinstance(sid, Sid) else Sid(id=sid)

			rows = (
				cls.session
				.query(cls)
				.filter(cls.id == v.id)
				.all()
			)

			for row in rows:
				cls.session.delete(row)
				removed = True

		return removed

	# Create or update atom from semantic id
	# ----------------------------------------------------------------------
	@classmethod
	def set(
		cls,
		sid    : Sid | int,
		text   : str,
		vector,
	) -> int:
		if text is None:
			raise ValueError('Text can not be None')

		if vector is None:
			raise ValueError('Vector can not be None')

		v = sid if isinstance(sid, Sid) else Sid(sid)

		row = cls(
			id          = v.id,
			document_id = v.document_id,
			text        = text,
			vector      = vector_serialize(vector)
		)

		cls.session.merge(row)

		return int(row.id)


# Relations
# --------------------------------------------------------------------------------
ww.db.Relations.add(
	ww.db.SemanticAtom, 'document',
	ww.db.SemanticDocument,
	back_populates='atoms'
)
