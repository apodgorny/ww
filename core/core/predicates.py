import typing, types, sys
from typing import List, Dict, Optional, Any, Union, get_args, get_origin
from pydantic import BaseModel

def is_optional(tp):
	return get_origin(tp) is Union and type(None) in get_args(tp)

def wrap_optional(tp):
	# Если tp уже Optional[...] — не трогаем
	if get_origin(tp) is Union and type(None) in get_args(tp):
		return tp
	return Optional[tp]

def unwrap_optional(tp):
	origin = get_origin(tp)
	if origin is Union:
		args = [a for a in get_args(tp) if a is not type(None)]
		if len(args) == 1:
			return unwrap_optional(args[0])
	return tp

def get_default(tp):
	tp     = unwrap_optional(tp)
	origin = get_origin(tp)

	if origin in (list, tuple, set, dict) : return origin()
	if tp     in (str, int, float, bool)  : return tp()

	try              : return tp()
	except Exception : return None

##############################################################################

def is_atomic_type(tp):
	# Atomic — int, str, float, bool
	tp = unwrap_optional(tp)
	return tp in (int, str, float, bool, complex)

def is_atomic(value):
	return is_atomic_type(type(value))

def is_atomic_list(tp):
	# Проверяем list[atomic]
	tp     = unwrap_optional(tp)
	origin = get_origin(tp)
	args   = get_args(tp)
	return origin in (list, List) and len(args) == 1 and is_atomic_type(args[0])

def is_atomic_dict(tp):
	# Проверяем dict[str, atomic]
	tp     = unwrap_optional(tp)
	origin = get_origin(tp)
	args   = get_args(tp)
	return origin in (dict, Dict) and len(args) == 2 and args[0] is str and is_atomic_type(args[1])

def is_pydantic(value):
		return isinstance(value, BaseModel)

def is_pydantic_class(tp):
	return isinstance(tp, type) and issubclass(tp, BaseModel)

def is_excluded_type(tp):
	# Nested Pydantic models are stored via edges
	# unwrap Optional[...] → T
	if get_origin(tp) is Union:
		args = [a for a in get_args(tp) if a is not type(None)]
		if len(args) == 1:
			tp = args[0]

	origin = get_origin(tp)
	args   = get_args(tp)

	if is_pydantic_class(tp)  : return True
	if origin in (list, List) : return len(args) == 1                    and is_pydantic_class(args[0])
	if origin in (dict, Dict) : return len(args) == 2 and args[0] is str and is_pydantic_class(args[1])

	return False

def is_list(tp):
	tp = unwrap_optional(tp)
	return get_origin(tp) in (list, List)

def is_dict(tp):
	tp = unwrap_optional(tp)
	return get_origin(tp) in (dict, Dict)

def is_annotation(obj):
	if isinstance(obj, type):
		return True
	# Python 3.9+: list[str], dict[str, int] → types.GenericAlias
	if sys.version_info >= (3, 9):
		if isinstance(obj, types.GenericAlias):
			return True
	# Python <3.9: typing.List[int], etc → typing._GenericAlias
	if hasattr(typing, '_GenericAlias') and isinstance(obj, typing._GenericAlias):
		return True
	return False
