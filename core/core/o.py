import json, yaml

from typing                                 import Any, get_args

from pydantic                               import BaseModel, model_validator, ValidationError
from pydantic_core                          import PydanticUndefined
from pydantic._internal._model_construction import ModelMetaclass

from .predicates                            import is_list, is_dict, unwrap_optional, is_annotation
from .o_field                               import OField
from .t                                     import T
from .odb                                   import ODB


################################################################################################################
# class OMeta
################################################################################################################


class OMeta(ModelMetaclass):
	# def __new__(mcs, name, bases, namespace, **kwargs):
	# 	annotations = dict(namespace.get('__annotations__', {}))
	# 	for fname, field in namespace.items():
	# 		if isinstance(field, OField) and 'type' in field.extra:
	# 			annotations[fname] = field.extra['type']
	# 	namespace['__annotations__'] = annotations
	# 	return super().__new__(mcs, name, bases, namespace, **kwargs)
	
	def __new__(mcs, name, bases, namespace, **kwargs):
		annotations = dict(namespace.get('__annotations__', {}))

		# 1. Upgrade all OField with 'type' in extra
		for fname, field in namespace.items():
			if isinstance(field, OField) and 'type' in field.extra:
				annotations[fname] = field.extra['type']

		# 2. Ensure every field has OField (including those with only annotation)
		for fname, tp in annotations.items():
			val = namespace.get(fname, None)
			if isinstance(val, OField):
				if val.get_type() is None:
					val.set_type(tp)      # set type!
			else:
				namespace[fname] = OField(tp, **kwargs)

		namespace['__annotations__'] = annotations
		o_class   = super().__new__(mcs, name, bases, namespace, **kwargs)
		o_class.__orm_class__ = T(T.PYDANTIC, T.SQLALCHEMY_MODEL, o_class)
		return o_class
		
	def __str__(cls):
		items = []
		for name, field in cls.model_fields.items():
			t        = field.annotation
			tname    = t.__name__                               if hasattr(t, '__name__')                     else str(t)
			default  = f'default={repr(field.default)}'         if field.default     is not PydanticUndefined else ''
			descr    = f'description={repr(field.description)}' if field.description is not None              else ''
			fattrs   = ', '.join([v for v in [default, descr] if v])
			def_part = f'= O.Field({fattrs})' if fattrs else ''

			items.append((name, tname, def_part))

			name_width = max(len(name)  for name, _, _  in items)
			type_width = max(len(tname) for _, tname, _ in items)

		lines = [f'class {cls.__name__}(O):']
		for name, tname, def_part in items:
			lines.append(f'    {name.ljust(name_width)} : {tname.ljust(type_width)}{def_part}')
		return '\n'.join(lines) + '\n'


################################################################################################################
# class O
################################################################################################################


class O(BaseModel, metaclass=OMeta):
	model_config = {
		'extra'              : 'forbid',
		'from_attributes'    : True,
		'is_persistent'      : False,
		'get_operator_class' : None
	}

	# Magic
	############################################################################

	def __init__(self, **kwargs):
		# Reserve id/global_name for DB lookups only.
		for k in ['id', 'global_name']:
			if k in kwargs:
				raise KeyError(f'Attribute `{k}` is reserved. Use `{self.__class__.__name__}.load({k})` instead')
			
		super().__init__(**kwargs)

	def __getattr__(self, name: str):
		if name in self.model_fields:
			raise AttributeError(name)

		related = self.db.get_related(name)
		if not related:
			raise AttributeError(f'{self.__class__.__name__} has no attribute or edge `{name}`')
		return related
	
	def __getitem__(self, key):
		if key in self.model_fields:
			return getattr(self, key)
		raise KeyError(key)

	def __setitem__(self, key, value):
		if key in self.model_fields:
			return setattr(self, key, value)
		raise KeyError(key)

	def __str__(self) -> str:
		return T(T.PYDANTIC, T.STRING, self)

	def __repr__(self):
		return f'<{self.__class__.__name__} id={self.id}>'

	# Public class methods
	############################################################################

	@model_validator(mode="before")
	@classmethod
	def _before_validate(cls, data):
		# Hook to mutate/inspect incoming data before validation.
		ValidationError.last_model = cls.__name__
		return cls.on_create(data)
	
	@classmethod
	def enable_persistence(cls, session):
		ODB.session = session
		O.model_config['is_persistent'] = True

	@classmethod
	def enable_instantiation(cls, get_operator_class):
		O.model_config['get_operator_class'] = get_operator_class

	@classmethod
	def on_create(cls, data):
		return data
	
	@classmethod
	def Field(cls, *args, **kwargs):
		# Shorthand to create an OField while staying on the O namespace.
		return OField(*args, **kwargs)

	@classmethod
	def has_field(cls, field: str) -> bool:
		return field in cls.model_fields
	
	@classmethod
	def has_table(cls):
		return ODB.table_exists(cls.__orm_class__.__tablename__)

	@classmethod
	def is_o_type(cls, tp: Any) -> bool:
		return isinstance(tp, type) and issubclass(tp, O)

	@classmethod
	def is_o_instance(cls, obj: Any) -> bool:
		return isinstance(obj, O)

	@classmethod
	def get_field_kind(cls, name, tp=None):
		tp = tp or cls.model_fields[name].annotation
		tp = unwrap_optional(tp)  # Всегда убираем Optional

		if O.is_o_type(tp):
			return 'single', tp

		if is_list(tp):
			sub = get_args(tp)[0]
			sub = unwrap_optional(sub)
			if O.is_o_type(sub):
				return 'list', sub

		if is_dict(tp):
			k, v = get_args(tp)
			v = unwrap_optional(v)
			if k is str and O.is_o_type(v):
				return 'dict', v

		return None, None

	@classmethod
	def to_schema_prompt(cls) -> str:
		return T(T.PYDANTIC, T.PROMPT, cls)

	@classmethod
	def to_jsonschema(cls) -> dict:
		return T(T.PYDANTIC, T.DEREFERENCED_JSONSCHEMA, cls)
	
	@classmethod
	def to_default(cls) -> 'O':
		'''
		Создаёт экземпляр схемы, заполнив все поля с заданными default/default_factory.
		Обязательные поля без дефолта будут пропущены — вызов может упасть, если они нужны.
		'''
		defaults = {
			name: field.get_default()
			for name, field in cls.model_fields.items()
			if field.get_default() is not ...
		}
		return cls.model_construct(**defaults)
	
	@classmethod
	def load(cls, ref: int | str) -> 'O':
		o = ODB.load(ref, cls)
		o.on_load()
		return o
	
	@classmethod
	def loader(cls, name):
		class Loader:
			def __init__(self, name, outer_cls):
				self.name = name
				self.cls  = outer_cls
			def __call__(self):
				return self.cls.load(self.name)
		return Loader(name, cls)
	
	@classmethod
	def get(cls, name) -> 'O':
		if cls.exists(name):
			return cls.load(name)
		return None
	
	@classmethod
	def all(cls, as_dict=False) -> dict[str, 'O']:
		items = ODB.all(cls)
		if as_dict:
			return {item.name: item for item in items}
		return items
	
	@classmethod
	def put(cls, name, **kwargs):
		o = cls.get(name)
		if o is None:
			o = cls(name=name, **kwargs)
		return o.set(**kwargs) # call the instance method
	
	@classmethod
	def pack(cls, args):
		return T(T.ARGUMENTS, T.PYDANTIC, cls, args)
	
	@classmethod
	def split(cls, by: str):
		'''
			Splits the schema into two:
			- MySchema__True  : fields where json_schema_extra[by] is True or missing
			- MySchema__False : fields where json_schema_extra[by] is explicitly False
			Returns (MySchema__True, MySchema__False)
		'''
		true_fields  = {}
		false_fields = {}
		for name, field in cls.model_fields.items():
			extra        = field.extra
			flag         = by(name, field) if callable(by) else extra.get(by, True)
			target       = false_fields if flag is False else true_fields
			desc         = extra.get('description', None)
			field_kwargs = dict(description=desc, json_schema_extra=extra)
			default      = field.get_default()
			target[name] = (field.annotation, default, field_kwargs)

		def make_schema(suffix, fields):
			annotations = {}
			namespace   = {}

			for k, (ann, default, field_kwargs) in fields.items():
				if default is PydanticUndefined: default = None
				annotations[k] = ann
				namespace[k]   = OField(default=default, **field_kwargs)

			namespace['__annotations__'] = annotations
			return type(f'{cls.__name__}__{suffix}', (O,), namespace)

		TrueSchema  = make_schema('True',  true_fields)
		FalseSchema = make_schema('False', false_fields)
		return TrueSchema, FalseSchema
	
	@classmethod
	def assert_instanceable(cls):
		if not 'get_operator_class' in O.model_config:
			raise RuntimeError(f'Could not create operator. Type `O` does not have instantiation enabled')
		if not cls.has_field('name'):
			raise RuntimeError(f'Could not create operator. Class `{cls.__name__}` does not have attribute `name`')
		if not cls.has_field('class_name'):
			raise RuntimeError(f'Could not create operator. Class `{cls.__name__}` does not have attribute `class_name`')
		
	@classmethod
	def exists(cls, name) -> bool:
		return ODB.exists(cls, name)
	
	@classmethod
	def schema(cls, *args, **fields):
		"""
			Dynamically create a new schema class inheriting from O.
			Usage:
				MySchema = O.schema(
					'MySchema',           # <- (опционально) имя схемы
					name = O.Field(str, default=''),
					age  = O.Field(int, default=0),
					title = str,
				)
				или без имени:
				MySchema = O.schema(
					title = str,
					...
				)
		"""
		annotations = {}
		namespace   = {}
		schema_name = 'AnonymousSchema'

		if args:
			if len(args) == 1 and isinstance(args[0], str):
				schema_name = args[0]
			else:
				raise TypeError('First and only arg to O.schema() must be schema name (str) if provided.')

		for fname, value in fields.items():
			if isinstance(value, OField):
				tp = value.get_type()
				if tp is None:
					raise ValueError(f'O.Field for `{fname}` must specify a type as first argument')
				annotations[fname] = tp
				namespace[fname]   = value
			elif is_annotation(value):
				annotations[fname] = value
				namespace[fname]   = O.Field(value)
			else:
				raise TypeError(
					f'Value for field `{fname}` must be O.Field(type, ...), or type/generic, got {type(value).__name__}'
				)
		namespace['__annotations__'] = annotations
		return type(schema_name, (cls,), namespace)
	
	@classmethod
	def describe(cls, except_keys=None):
		# Produce a human-readable bullets list for fields (minus except_keys).
		except_keys = set(except_keys or [])
		lines = []
		fields = [k for k in cls.model_fields if k not in except_keys]
		for i, k in enumerate(fields):
			field = cls.model_fields[k]
			label = k
			descr = field.description or ''
			if descr and descr.endswith('.'):
				descr = descr[:-1]
			prefix = '-' if i == 0 else '\t-'
			lines.append(f'{prefix} {label}: {descr}')
		return '\n'.join(lines)

	# Getters
	############################################################################

	@property
	def db(self):
		if O.model_config['is_persistent']:
			return ODB(self)
		raise RuntimeError(f'Could not connect to session: persistence is not enabled in `O`')
	
	@property
	def id(self):
		return self.__dict__.get('__id__')

	# Public
	############################################################################

	def to_prompt(self)                 -> str       : return self.to_json()
	def to_json(self, r=False)          -> str       : return json.dumps(self.to_dict(r, e=True), indent=4, ensure_ascii=False)
	def to_yaml(self, r=False, e=False) -> str       : return yaml.dump(self.to_dict(r=r, e=e), allow_unicode=True, sort_keys=False)
	def to_dict(self, r=False, e=False) -> dict      : return T(T.PYDANTIC, T.DATA, self, recursive=r, show_empty=e)
	def to_tree(self)                   -> str       : return T(T.PYDANTIC, T.TREE, self)
	def to_schema(self)                 -> type      : return self.__class__
	def keys(self)                      -> list[str] : return list(self.model_fields.keys())
	def unpack(self)                                 : return T(T.PYDANTIC, T.ARGUMENTS, self)

	def on_save(self): return self
	def on_load(self): return self	

	def to_operator(self):
		self.assert_instanceable()
		return O.model_config['get_operator_class'](self.class_name)(self.name, self)

	def to_semantic_hint(self) -> str:
		data   = T(T.PYDANTIC, T.DATA, self)
		fields = self.model_fields
		lines  = []

		for name, value in data.items():
			info = fields[name].json_schema_extra or {}
			if info.get('semantic') and value is not None:
				lines.append(f'{name}: {value}')

		return ' | '.join(lines)
	
	def set(self, **kwargs):
		for k, v in kwargs.items():
			if k != 'id':
				setattr(self, k, v)
		self.save()
		return self

	def clone(self):
		data = self.to_dict()
		data.pop('id', None)
		return self.__class__(**data)

	def save(self):
		self.on_save()
		self.db.save()
		return self

	def delete(self):
		self.db.delete()

	def get_description(self, field: str) -> str:
		info = self.model_fields.get(field)
		return info.description or ''
	
	def iter(self):
		for name, field in self.model_fields.items():
			value = getattr(self, name, None)
			yield name, value, field
	
	def iter_nested(self):
		'''
			Yields (key, val) for all nested O-objects in single/list/dict fields (first level only).
			key:
				- None for 'single'
				- index (int) for 'list'
				- dict key for 'dict'
		'''
		for name, field in self.model_fields.items():
			kind, _ = self.get_field_kind(name, field.annotation)
			val = getattr(self, name, None)
			if val is PydanticUndefined or val is None:
				continue
			if kind == 'single' and val is not None:
				yield ('', val)
			elif kind == 'list' and val:
				for idx, item in enumerate(val):
					yield (str(idx), item)
			elif kind == 'dict' and val:
				for k, item in val.items():
					yield (k, item)


################################################################################################################
# ValidationError
################################################################################################################


from pydantic import ValidationError

def humanize(self):
	lines = [f'In `{ValidationError.last_model}`']
	for e in self.errors():
		var = '.'.join(str(x) for x in e.get('loc', [])) or 'unknown'
		t1  = e.get('type', 'unknown')
		v1  = e.get('input', 'unknown')
		t2  = type(v1).__name__ if v1 != 'unknown' else 'unknown'
		v1  = str(v1)
		if len(v1) > 300:
			v1 = v1[:300] + ' ...'
		if t1 == 'missing':
			line = f'  - `{var}`: is missing'
		elif t1 == 'extra_forbidden':
			line = f'  - `{var}`: is unexpected'
		else:
			line = f'  - `{var}`: expected `{t1}`, got `{t2}({v1})`'
		lines.append(line)
	return '\n'.join(lines)

def validationerror_str(self):
	return self.humanize()

ValidationError.humanize = humanize
ValidationError.__str__  = validationerror_str
ValidationError.__repr__ = validationerror_str
