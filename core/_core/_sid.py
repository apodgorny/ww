# ======================================================================
# Canonical semantic id (Sid): 4 × 16-bit layout
# [ domain | doc | item | reserved ]
# ======================================================================

_MASK = 0xFFFF

_SHIFT_ITEM   = 16
_SHIFT_DOC    = 32
_SHIFT_DOMAIN = 48


class Sid:
	'''
	Opaque, immutable semantic address.
	Encodes (domain_id, document_id, item_id) into a single integer.
	No querying. No state. No policy.
	'''

	# Construct Sid from full integer or semantic components.
	# ------------------------------------------------------------------
	def __init__(
		self,
		sid         : int | None = None,
		*,
		domain_id   : int | None = None,
		document_id : int | None = None,
		item_id     : int | None = None,
	):
		if sid is None:
			sid = (
				((domain_id   or 0) & _MASK) << _SHIFT_DOMAIN |
				((document_id or 0) & _MASK) << _SHIFT_DOC    |
				((item_id     or 0) & _MASK) << _SHIFT_ITEM
			)

		self.id = int(sid)

	# Convert Sid to integer.
	# ------------------------------------------------------------------
	def __int__(self):
		return self.id

	# Hash Sid by its integer value.
	# ------------------------------------------------------------------
	def __hash__(self):
		return hash(self.id)

	# Compare Sid with Sid or int.
	# ------------------------------------------------------------------
	def __eq__(self, other):
		result = False

		if isinstance(other, Sid):
			result = self.id == other.id
		elif isinstance(other, int):
			result = self.id == other

		return result

	# Human-readable representation.
	# ------------------------------------------------------------------
	def __repr__(self):
		return (
			f'Sid(domain={self.domain_id}, '
			f'doc={self.document_id}, '
			f'item={self.item_id})'
		)

	# ==================================================================
	# PUBLIC METHODS
	# ==================================================================

	# Ids are sequential, get document id range
	# ------------------------------------------------------------------
	@staticmethod
	def get_document_id_range(document_id):
		min = document_id << _SHIFT_DOC
		max = ((document_id + 1) << _SHIFT_DOC) - 1
		return min, max

	# Ids are sequential, get domain id range
	# ------------------------------------------------------------------
	@staticmethod
	def get_domain_id_range(domain_id):
		min = domain_id << _SHIFT_DOMAIN
		max = ((domain_id + 1) << _SHIFT_DOMAIN) - 1
		return min, max

	# Domain component of Sid.
	# ------------------------------------------------------------------
	@property
	def domain_id(self) -> int:
		value = (self.id >> _SHIFT_DOMAIN) & _MASK
		return value

	# Document component of Sid.
	# ------------------------------------------------------------------
	@property
	def document_id(self) -> int:
		value = (self.id >> _SHIFT_DOC) & _MASK
		return value

	# Item component of Sid.
	# ------------------------------------------------------------------
	@property
	def item_id(self) -> int:
		value = (self.id >> _SHIFT_ITEM) & _MASK
		return value
