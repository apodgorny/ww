import os, json, inspect
from datetime import datetime

import ww


class OperatorMeta(type(ww.Module)):

	def __call__(cls, *args, **kwargs):
		inst = super().__call__()
		return inst.__invoke__(*args, **kwargs)

	def __new__(mcls, name, bases, namespace):
		cls = super().__new__(mcls, name, bases, namespace)

		for attr_name, attr in namespace.items():
			if not attr_name.startswith('_'):
				if inspect.isfunction(attr):
					if not inspect.iscoroutinefunction(attr):
						raise TypeError(f'Method `{name}.{attr_name}` must be async')
		return cls


class Operator(ww.Module, metaclass=OperatorMeta):

	async def __invoke__(self, *args, **kwargs):
		await self.initialize()
		return await self.invoke(*args, **kwargs)

	async def initialize(self):
		raise NotImplementedError

	async def invoke(self, *args, **kwargs):
		raise NotImplementedError
