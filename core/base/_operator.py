import os, json
from datetime import datetime

import ww


class Operator(ww.Module):
	def __init__(self, name=None):
		self.name = name if name else self.__class__.__name__
	
	def __repr__(self) -> str:
		return f'<Operator {self.name}>'

	async def __call__(self, *args, **kwargs):
		await self.init()
		return await self.invoke(*args, **kwargs)

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	async def init(self):
		pass

	async def invoke(self, *args, **kwargs):
		raise NotImplementedError('Operator must implement invoke method')

