import copy, re, json
from typing import Any, get_args, get_origin, Union, List, Dict

from pydantic        import BaseModel, create_model
from pydantic_core   import PydanticUndefined
from sqlalchemy      import Table, Column, MetaData, Integer, String, JSON, text
from sqlalchemy.orm  import declarative_base

from .predicates            import is_atomic_dict, is_atomic_list, is_pydantic, is_pydantic_class, is_excluded_type, is_atomic
from .transform             import T
from .string                import String as S
from wordwield.core.base.record import Record
from .o_field               import OField


T.PYDANTIC(BaseModel)
T.JSONSCHEMA(dict)
T.DEREFERENCED_JSONSCHEMA(dict)
T.DATA()
T.ARGUMENTS(None)
T.SQLALCHEMY_MODEL(object)
T.PROMPT(str)
T.FIELD(OField)
T.TYPE(str)
T.STRING(str)
T.TREE(dict)


@T.register(T.PYDANTIC, T.STRING)
def model_to_string(obj, base_level=0):
	tab_size = 3
	label    = f'{obj.name}:' if hasattr(obj, 'name') else ''
	id_str   = f'({label}{obj.id})' if obj.id else ''
	data     = obj.to_dict(r=False, e=True)

	def fmt_value(value, level):
		if isinstance(value, BaseModel):
			# For nested BaseModel, don't add extra indentation - it handles its own
			nested = model_to_string(value, 0)
			# Indent the entire nested string to the current level
			lines = nested.splitlines()
			indented_lines = []
			for line in lines:
				if line.strip():  # Only indent non-empty lines
					indented_lines.append(' ' * (level * tab_size) + line)
				else:
					indented_lines.append('')
			return '\n'.join(indented_lines)
		if isinstance(value, list):
			if not value:
				return '[]'
			items = []
			for v in value:
				formatted = fmt_value(v, level + 1)
				# Don't add extra indentation for BaseModel items since they handle their own
				if isinstance(v, BaseModel):
					items.append(formatted)
				else:
					items.append(' ' * ((level + 1) * tab_size) + formatted)
			return '[\n' + ',\n'.join(items) + '\n' + ' ' * (level * tab_size) + ']'
		if isinstance(value, dict):
			if not value:
				return '{}'
			items = []
			for k, v in value.items():
				formatted = fmt_value(v, level + 1)
				items.append(' ' * ((level + 1) * tab_size) + f'"{k}": {formatted}')
			return '{\n' + ',\n'.join(items) + '\n' + ' ' * (level * tab_size) + '}'
		return json.dumps(value, ensure_ascii=False)

	# Build the object representation
	base_indent = ' ' * (base_level * tab_size)
	field_indent = ' ' * ((base_level + 1) * tab_size)
	
	lines = [base_indent + f'{obj.__class__.__name__}{id_str} {{']
	
	items = list(data.items())
	for i, (k, v) in enumerate(items):
		is_last = i == len(items) - 1
		comma   = '' if is_last else ','
		if v is not None:
			formatted = fmt_value(v, base_level + 1)
			lines.append(field_indent + f'"{k}": {formatted}{comma}')
	
	lines.append(base_indent + '}')
	result = '\n'.join(lines)
	
	# Clean up extra spaces after colons
	return re.sub(':[ ]+', ': ', result)

@T.register(T.PYDANTIC, T.JSONSCHEMA)
def model_to_jsonschema(model: type[BaseModel]) -> dict:
	return model.model_json_schema()


@T.register(T.PYDANTIC, T.DATA)
def model_to_data(obj, recursive=False, show_empty=False):
	def convert(value, seen):
		if is_pydantic(value):
			if recursive:
				if id(value) in seen:
					return None
				seen.add(id(value))
				return {
					k: convert(v, seen)
					for k, v in value.model_dump().items()
				}
			else:
				return None

		if isinstance(value, dict):
			return {
				k: convert(v, seen)
				for k, v in value.items()
				if recursive or not is_pydantic(v)
			}

		if isinstance(value, (list, tuple, set)):
			return [
				convert(v, seen)
				for v in value
				if recursive or not is_pydantic(v)
			]

		return value

	if is_pydantic(obj):
		if not recursive:
			return {
				k: getattr(obj, k)
				for k, f in obj.model_fields.items()
				if show_empty or not is_excluded_type(f.annotation)
			}
		return convert(obj, seen=set())

	return convert(obj, seen=set())


@T.register(T.JSONSCHEMA, T.DEREFERENCED_JSONSCHEMA)
def dereference_schema(schema: dict) -> dict:
	def resolve_refs(obj, defs):
		if isinstance(obj, dict):
			if '$ref' in obj:
				ref_name = obj['$ref'].split('/')[-1]
				
				# Try from $defs
				if ref_name in defs:
					return resolve_refs(defs[ref_name], defs)

				# Try from globals (must be a Pydantic model)
				if ref_name in globals():
					ref_cls = globals()[ref_name]
					if hasattr(ref_cls, 'model_json_schema'):
						return resolve_refs(ref_cls.model_json_schema(), defs)

				# Fallback: raise error
				raise TypeError(f'Referenced type `{ref_name}` not found in $defs or globals()')

			return {k: resolve_refs(v, defs) for k, v in obj.items()}

		elif isinstance(obj, list):
			return [resolve_refs(item, defs) for item in obj]

		else:
			return obj

	copied = copy.deepcopy(schema)
	defs   = copied.pop('$defs', {})
	return resolve_refs(copied, defs)
	

@T.register(T.PYDANTIC, T.ARGUMENTS)
def pydantic_to_arguments(model):
	fields = list(model.model_fields)
	args = tuple(getattr(model, k) for k in fields)
	return args[0] if len(args) == 1 else args

@T.register(T.ARGUMENTS, T.PYDANTIC)
def arguments_to_pydantic(model_cls, args):
	fields = list(model_cls.model_fields)
	if isinstance(args, tuple):
		args = dict(zip(fields, args))
	elif not isinstance(args, dict) and len(fields) == 1:  # Single value
		args = {fields[0]: args}
	return model_cls(**args)



######################################## SQLALCHEMY ########################################


# @T.register(T.PYDANTIC, T.SQLALCHEMY_MODEL)
# def pydantic_to_sqlalchemy_model(model: type[BaseModel]) -> type:
# 	fields = {}

# 	if issubclass(model, BaseModel):
# 		fields['id'] = Column(Integer, primary_key=True, autoincrement=True)

# 		for name, field in model.model_fields.items():
# 			is_id_field = name == 'id'                   # Skip 'id' — already handled
# 			ftype       = field.annotation               # Raw field type
# 			excluded    = is_excluded_type(ftype)        # Nested Pydantic models are stored via edges

# 			if not is_id_field and not excluded:
# 				for name, field in model.model_fields.items():
# 					ftype = field.annotation
# 					if is_atomic_list(ftype) or is_atomic_dict(ftype):
# 						sql_type = JSON
# 					elif ftype is int:
# 						sql_type = Integer
# 					elif ftype is str:
# 						sql_type = String
# 					elif ftype is dict:
# 						sql_type = JSON
# 					else:
# 						sql_type = String
# 					fields[name] = Column(sql_type, nullable=not field.is_required())

# 		name  = model.__name__ + 'Orm'
# 		table = type(name, (Record,), {
# 			'__tablename__'  : model.__name__.lower(),
# 			'__table_args__' : {
# 				'extend_existing'      : True,
# 				'sqlite_autoincrement' : True
# 			},
# 			**fields
# 		})

# 	else:
# 		table = model  # Already a table — passthrough

# 	return table


@T.register(T.PYDANTIC, T.SQLALCHEMY_MODEL)
def pydantic_to_sqlalchemy_model(model: type[BaseModel]) -> type:
	fields = {}

	if issubclass(model, BaseModel):
		fields['id'] = Column(Integer, primary_key=True, autoincrement=True)

		for name, field in model.model_fields.items():
			if name == 'id':
				continue

			ftype    = field.annotation
			excluded = is_excluded_type(ftype)

			if not excluded:
				column_kwargs = {}
				if is_atomic_list(ftype) or is_atomic_dict(ftype):
					sql_type = JSON
				elif ftype is int:
					sql_type = Integer
				elif ftype is bool:
					sql_type = Integer
					column_kwargs['nullable'] = False
					column_kwargs['default']  = 0
					column_kwargs['server_default'] = text('0')
					column_kwargs['info'] = {'is_bool': True}

				elif ftype is dict:
					sql_type = JSON
				else:
					sql_type = String

				column_kwargs = {'nullable': not field.is_required()}
				if name == 'name':
					column_kwargs['unique'] = True

				fields[name] = Column(sql_type, **column_kwargs)

		name  = model.__name__ + 'Orm'
		table = type(name, (Record,), {
			'__tablename__'  : model.__name__.lower(),
			'__table_args__' : {
				'extend_existing'      : True,
				'sqlite_autoincrement' : True
			},
			**fields
		})

	else:
		table = model  # Already a table — passthrough

	return table


@T.register(T.SQLALCHEMY_MODEL, T.PYDANTIC)
def sqlalchemy_model_to_pydantic(orm_cls: type) -> type[BaseModel]:
	fields = {}

	for col in orm_cls.__table__.columns:
		if   isinstance(col.type, Integer) : py_type = int
		elif isinstance(col.type, String)  : py_type = str
		else                               : py_type = str  # fallback

		required = col.nullable is False and col.default is None and not col.autoincrement
		default  = ... if required else None

		field = OField(py_type, default=default, description=str(col.comment or ''))
		fields[col.name] = (py_type, field)

	name = orm_cls.__name__.replace('Orm', '') + 'Schema'
	return create_model(name, **fields)


@T.register(T.SQLALCHEMY_MODEL, T.DATA)
def sqlalchemy_model_to_data(obj):
	if not hasattr(obj, '__table__'):
		raise TypeError(f'❌ Expected SQLAlchemy model, got: {type(obj)} → {obj}')
	columns = set(obj.__table__.columns.keys())
	data    = {}
	for k in columns:
		val = getattr(obj, k)
		if val is PydanticUndefined:
			continue  # skip 
		data[k] = val
	return data

######################################## TYPE ########################################

@T.register(T.TYPE, T.STRING)
def type_to_string(tp: Any) -> str:
	origin = get_origin(tp)
	args   = get_args(tp)

	if origin is Union and type(None) in args:
		non_none = [a for a in args if a is not type(None)]
		return T(T.TYPE, T.STRING, non_none[0])

	if origin in (list, List):
		item_type = args[0] if args else Any
		item_str  = T(T.TYPE, T.STRING, item_type)
		return f'List[{item_str}]'

	if origin in (dict, Dict):
		key_type   = args[0] if args else Any
		value_type = args[1] if len(args) > 1 else Any
		key_str    = T(T.TYPE, T.STRING, key_type)
		val_str    = T(T.TYPE, T.STRING, value_type)
		return f'Dict[{key_str}, {val_str}]'

	if hasattr(tp, '__name__'):
		return tp.__name__
		# name = tp.__name__
		# return f'"{name}"' if name == 'str' else name

	return str(tp)

@T.register(T.TYPE, T.PROMPT)
def type_to_prompt(tp: Any, indent: int = 0) -> str:
	origin = get_origin(tp)
	args   = get_args(tp)

	# Optional[X]
	if origin is Union and type(None) in args:
		non_none = [a for a in args if a is not type(None)]
		return T(T.TYPE, T.PROMPT, non_none[0], indent)

	# List[T] (with recursive support)
	if origin in (list, List):
		item_type = args[0] if args else Any
		if hasattr(item_type, 'model_fields'):
			body   = T(T.TYPE, T.PROMPT, item_type, indent + 1)
			pad    = '  ' * (indent + 1)
			lines  = body.splitlines()
			indented = '\n'.join(pad + line for line in lines)
			return '[\n' + indented + '\n' + '  ' * indent + ', ... ]'
		else:
			type_str = T(T.TYPE, T.STRING, item_type)
			return f'[ {type_str} ]'

	# Dict[...] (fallback only)
	if origin in (dict, Dict):
		key_type   = args[0] if args else Any
		value_type = args[1] if len(args) > 1 else Any
		key_name   = T(T.TYPE, T.STRING, key_type)
		val_str    = T(T.TYPE, T.PROMPT, value_type, indent + 1)
		return f'{{ "{key_name}": {val_str} }}'

	# Submodel
	if hasattr(tp, 'model_fields'):
		return T(T.PYDANTIC, T.PROMPT, tp, indent)

	return T(T.TYPE, T.STRING, tp)


@T.register(T.FIELD, T.PROMPT)
def field_to_prompt(field: OField, indent: int = 0) -> str:
	comment = f"  # {' '.join(field.description.split())}" if field.description else ''
	value   = T(T.TYPE, T.PROMPT, field.annotation, indent + 1)
	pad     = '  ' * indent
	return f'{pad}"{field.title}": {value}{comment}'


@T.register(T.PYDANTIC, T.PROMPT)
def pydantic_to_prompt(model_cls: type[BaseModel], indent: int = 0) -> str:
	lines = []
	pad = '  ' * indent
	lines.append(pad + '{')
	for name, field in model_cls.model_fields.items():
		field.title = name
		lines.append(T(T.FIELD, T.PROMPT, field, indent + 1))
	lines.append(pad + '}')
	return '\n'.join(lines)


@T.register(T.DATA, T.TREE)
def data_to_tree(data: dict, root='', color=False):
	lines = []
	S0 = '    '
	S1 = '│   '
	S2 = '└── '
	S3 = '├── '

	def add(margin, key='', spacing='', value=None):
		lines.append({'margin': margin, 'key': key, 'spacing': spacing, 'value': value})

	def walk(node, margin='', key=None, is_last=True, key_pad=0, prev_type=None):
		connector = S2 if is_last else S3
		disp_key  = key if key is not None else ''
		if isinstance(node, dict):
			# Insert a blank line before section if previous sibling was not dict and not root
			if prev_type not in (None, dict) and (disp_key or margin):
				add(margin + (S1 if not is_last else S0))
			# Compute max key width for leaves at this level
			leaf_keys = [k for k, v in node.items() if is_atomic(v)]
			maxlen = max((len(str(k)) for k in leaf_keys), default=0)
			# Add section header line
			if disp_key or margin:
				add(margin + connector, disp_key, '', None)
			keys = list(node.keys())
			prev = None
			for i, k in enumerate(keys):
				val         = node[k]
				is_leaf     = is_atomic(val)
				last        = i == len(keys) - 1
				next_margin = margin + (S0 if is_last else S1)
				walk(val, next_margin, k, last, maxlen if is_leaf else 0, prev)
				prev = type(val)
			# Margin-aware blank line after section unless it's last
			if not is_last:
				add(margin + S1)
		elif is_atomic(node):
			pad = ' ' * (key_pad - len(str(disp_key))) if key_pad else ''
			add(margin + (S2 if is_last else S3), disp_key, pad, repr(node))
		elif isinstance(node, list):
			if disp_key or margin:
				add(margin + (S2 if is_last else S3), disp_key, '', None)
			for i, item in enumerate(node):
				last        = i == len(node) - 1
				next_margin = margin + (S0 if is_last else S1)
				walk(item, next_margin, f'[{i}]', last, prev_type=type(node))
		else:
			add(margin + (S2 if is_last else S3), disp_key, '', repr(node))

	if root:
		add('', root, '', None)
		add(S1)
		keys           = list(data.keys())
		root_leaf_keys = [k for k, v in data.items() if is_atomic(v)]
		root_key_pad   = max((len(str(k)) for k in root_leaf_keys), default=0)
		prev           = None
		for i, k in enumerate(keys):
			last    = i == len(keys) - 1
			val     = data[k]
			is_leaf = is_atomic(val)
			walk(val, '', k, last, root_key_pad if is_leaf else 0, prev)
			prev = type(val)
	else:
		walk(data, '', None, True)

	def render_line(entry):
		m, k, s, v = (entry[k] for k in ['margin','key','spacing','value'])
		if color:
			if m: m = S.color(m, S.GRAY)
			if k: k = S.color(k, S.YELLOW)
			eq = S.color(' = ', S.GRAY)
			if isinstance(v, str):
				v = re.sub(r'\(([^)]+)\)', lambda m: f'({S.color(m.group(1), S.BLUE)})', v)
		else:eq = ' = '

		if   v is not None : return f'{m}{k}{s}{eq}{v}'
		elif k             : return f'{m}{k}'

		return m  # margin-only line

	return '\n' + '\n'.join(render_line(e) for e in lines) + '\n'
