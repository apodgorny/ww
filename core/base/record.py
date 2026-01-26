import enum, json
from datetime import date, datetime

from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm             import declarative_base

Base: DeclarativeMeta = declarative_base()


class Record(Base):
	__abstract__ = True

	def __str__(self):
		return self.__repr__()

	def __repr__(self):
		id_str = f'({self.id})' if self.id else ''
		return f'{self.__class__.__name__}{id_str}: ' + self.to_json()

	# Convenience: add this instance to the global session
	# ----------------------------------------------------------------------
	def add(self, flush=True):
		self.session.add(self)
		if flush:
			self.session.flush()
		return self

	# Convenience: delete this instance from the global session
	# ----------------------------------------------------------------------
	def delete(self, flush=True):
		self.session.delete(self)
		if flush:
			self.session.flush()

	@staticmethod
	def _json_default(obj):
		if isinstance(obj, (datetime, date)):
			return obj.isoformat()
		return str(obj)  # fallback

	def to_json(self) -> str:
		return json.dumps(
			self.to_dict(),
			ensure_ascii = False,
			indent       = 4,
			default      = self._json_default
		)

	def to_dict(self) -> dict[str, any]:
		result = {}
		for c in self.__table__.columns:
			value = getattr(self, c.name)
			if isinstance(value, enum.Enum):
				value = value.value
			result[c.name] = value
		return result

	@classmethod
	def from_dict(cls, data: dict[str, any]) -> 'TableBase':
		return cls(**data)
