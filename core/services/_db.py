# ======================================================================
# Database initialization and low-level DB service for ww (Core only)
# ======================================================================

import os

from sqlalchemy import create_engine, inspect, text

import ww, yo


class Db(yo.base.Service):

	# ------------------------------------------------------------------
	# Initialize DB engine and connection
	# ------------------------------------------------------------------
	def initialize(self):
		self.engine  = None
		self.conn    = None
		self.path    = ww.Conf.DB_PATH
		self._tx     = None
		self._depth  = 0

		db_url = f'sqlite:///{self.path}'

		parent_dir = os.path.dirname(self.path) or '.'
		if not os.access(parent_dir, os.W_OK):
			raise RuntimeError(
				f'Cannot create DB file: Directory `{parent_dir}` is not writable.'
			)

		self.engine = create_engine(
			db_url,
			connect_args = {'check_same_thread': False},
			echo         = False,
		)

		self.conn = self.engine.connect()

		self.print(f'Database initialized at {self.path}')

	# ------------------------------------------------------------------
	# Schema helpers (DB-level only)
	# ------------------------------------------------------------------
	def create_table(self, sql: str):
		self.conn.execute(text(sql))

	def delete_table(self, table_name: str):
		self.conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))

	def delete_all(self):
		inspector = inspect(self.engine)
		with self.engine.begin() as conn:
			for table_name in inspector.get_table_names():
				conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))

		self.print('All tables dropped (DB file retained)')

	# ------------------------------------------------------------------
	# Transaction control (explicit, stack-based)
	# ------------------------------------------------------------------
	def start_tx(self):
		if self._depth == 0:
			self._tx = self.conn.begin()
		self._depth += 1

	def end_tx(self):
		self._depth -= 1
		if self._depth == 0 and self._tx is not None:
			self._tx.commit()
			self._tx = None

	def rollback(self):
		if self._tx is not None:
			self._tx.rollback()
			self._tx = None
		self._depth = 0

	# ------------------------------------------------------------------
	# Raw execution helpers (used by recordsets, not records)
	# ------------------------------------------------------------------
	def upsert(self, sql: str, params: dict | None = None):
		result = self.conn.execute(text(sql), params or {})
		return result.lastrowid

	def select(self, sql: str, params: dict | None = None):
		return self.conn.execute(text(sql), params or {}).fetchall()

	def delete(self, sql: str, params: dict | None = None):
		self.conn.execute(text(sql), params or {})
