import types

from pydantic.fields import FieldInfo
from pydantic_core   import PydanticUndefined

from .predicates     import is_annotation, get_default, is_optional, wrap_optional


class OField(FieldInfo):
	def __init__(self, *args, default=PydanticUndefined, default_factory=PydanticUndefined, description='', **kwargs):
		extra = kwargs.pop('json_schema_extra', {}) or {}
		if description:
			extra['description']  = description
			kwargs['description'] = description

		self._type = PydanticUndefined
		if args:
			if is_annotation(args[0]):
				args = list(args)
				self._type = args.pop()
		if args:
			raise RuntimeError(f'OField: Unexpected positional args: {args}')
		
		if self._type is not PydanticUndefined:
			has_default = default is not PydanticUndefined or default_factory is not PydanticUndefined
			if has_default and not is_optional(self._type):
				self._type = wrap_optional(self._type)

		# Если дефолт не задан И поле Optional — делаем default=None
		if self._type is not PydanticUndefined and is_optional(self._type):
			if default is PydanticUndefined and default_factory is PydanticUndefined:
				default = None

		# Pass all non-service kwargs into extra
		for k, v in dict(kwargs).items():
			if not (isinstance(v, type) or isinstance(v, types.FunctionType)):
				extra[k] = v
			if k not in ['default', 'default_factory', 'description']:
				kwargs.pop(k)

		init_kwargs = {'json_schema_extra': extra}
		if description:
			init_kwargs['description'] = description

		# Correct logic for defaults:
		if default is not PydanticUndefined:
			init_kwargs['default'] = default
		elif default_factory is not PydanticUndefined:
			init_kwargs['default_factory'] = default_factory
		elif self._type is not PydanticUndefined:
			def_val = get_default(self._type)
			if isinstance(def_val, (list, dict, set)):
				init_kwargs['default_factory'] = lambda: get_default(self._type)
			else:
				init_kwargs['default'] = def_val

		super().__init__(**init_kwargs)
	@property
	def extra(self):
		return self.json_schema_extra or {}
	
	def set_type(self, t):
		self._type = t

	def get_type(self):
		return getattr(self, '_type', None)

	def get_default(self, *args, **kwargs):
		# Совместимость с Pydantic: всегда возвращаем дефолт или фабрику
		if getattr(self, 'default', None) is not None:
			return self.default
		if getattr(self, 'default_factory', None) is not None:
			return self.default_factory()
		
		return None
