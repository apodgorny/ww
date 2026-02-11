from typing import ClassVar, Any
from pydantic import BaseModel, model_validator

import ww


class DbRecord(BaseModel):
	"""
	Live DB-backed record.
	- DTO
	- validated object
	- persistence-aware
	"""

	# ---- Static contract ----
	__table__ : ClassVar[str]
	__pk__    : ClassVar[str | tuple[str, ...]]

	# ---- Runtime wiring ----
	_db : ClassVar = ww.services.Db


	# ==================================================================
	# Core helpers
	# ==================================================================

	def _values(self) -> dict[str, Any]:
		"""Values to persist"""
		return self.model_dump(exclude_none=True)

	def _pk_fields(self) -> tuple[str, ...]:
		if isinstance(self.__pk__, str):
			return (self.__pk__,)
		return tuple(self.__pk__)

	def _pk_where(self) -> dict[str, Any]:
		where = {}
		for k in self._pk_fields():
			v = getattr(self, k, None)
			if v is None:
				raise ValueError(f'Primary key `{k}` is None')
			where[k] = v
		return where

	def _apply_pk(self, pk):
		"""
		Apply returned pk to self.
		Supports:
		- single int
		- dict of pk fields
		"""
		if pk is None:
			return

		if isinstance(pk, dict):
			for k, v in pk.items():
				setattr(self, k, v)
		else:
			setattr(self, self._pk_fields()[0], pk)


	# ==================================================================
	# Persistence
	# ==================================================================

	def save(self):
		"""
		Insert or update.
		Always validated.
		"""
		self.model_validate(self.model_dump())

		pk = self._db.upsert(
			self.__table__,
			self._values(),
			self._pk_fields(),
		)

		self._apply_pk(pk)
		return self

	def delete(self):
		self._db.delete(
			self.__table__,
			self._pk_where(),
		)
		return True


	# ==================================================================
	# Loading
	# ==================================================================

	@classmethod
	def select(cls, **where):
		rows = cls._db.select(
			cls.__table__,
			where = where or None
		)
		return [cls(**row) for row in rows]

	@classmethod
	def get(cls, **where):
		rows = cls.select(**where)
		return rows[0] if rows else None
