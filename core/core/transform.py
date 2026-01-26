from collections import defaultdict
from typing      import Callable, Any


class _Transform:
	def __init__(self):
		self._registry : dict[str, dict[str, Callable]] = defaultdict(dict)
		self._shapes   : dict[str, dict]                = {}

	def __call__(self, from_shape: str, to_shape: str, thing: Any, *args, **kwargs):
		steps = self._resolve_path(from_shape, to_shape)
		for step in steps:
			thing = step(thing, *args, **kwargs)
		return thing

	def __getattr__(self, name: str):
		if name.isupper():
			def declare(type_: type=None, validate: Callable = None):
				if name not in self._shapes:
					self._shapes[name] = {
						'type'    : type_,
						'validate': validate or (lambda x: isinstance(x, type_))
					}
					setattr(self, name, name)
				return name
			return declare
		raise AttributeError(f"T has no attribute '{name}'")

	#######################################################################

	def _resolve_path(self, from_shape: str, to_shape: str) -> list[Callable]:
		if from_shape == to_shape:
			return [lambda x: x]

		visited = set()
		queue   = [(from_shape, [])]

		while queue:
			current, path = queue.pop(0)
			if current in visited:
				continue
			visited.add(current)

			for neighbor in self._registry.get(current, {}):
				step = self._registry[current][neighbor]
				if neighbor == to_shape:
					return path + [step]
				else:
					queue.append((neighbor, path + [step]))

		raise ValueError(f"No transformation path from {from_shape} to {to_shape}")

	#######################################################################

	def register(self, from_shape: str, to_shape: str):
		def decorator(fn: Callable):
			if from_shape not in self._shapes:
				raise ValueError(f"Unknown shape: {from_shape}")
			if to_shape not in self._shapes:
				raise ValueError(f"Unknown shape: {to_shape}")
			self._registry[from_shape][to_shape] = fn
			return fn
		return decorator

	def available(self) -> dict[str, list[str]]:
		return {src: list(dests) for src, dests in self._registry.items()}


# 🎯 Singleton
T = _Transform()
