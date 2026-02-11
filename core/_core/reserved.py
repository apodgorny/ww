def is_reserved(s):
	return s in [
		# Keywords
		'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
		'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
		'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
		'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return',
		'try', 'while', 'with', 'yield',

		# Built-in functions
		'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'breakpoint', 'bytearray', 'bytes',
		'callable', 'chr', 'classmethod', 'compile', 'complex', 'delattr', 'dict',
		'dir', 'divmod', 'enumerate', 'eval', 'exec', 'filter', 'float', 'format',
		'frozenset', 'getattr', 'globals', 'hasattr', 'hash', 'help', 'hex', 'id',
		'input', 'int', 'isinstance', 'issubclass', 'iter', 'len', 'list', 'locals',
		'map', 'max', 'memoryview', 'min', 'next', 'object', 'oct', 'open', 'ord',
		'pow', 'print', 'property', 'range', 'repr', 'reversed', 'round', 'set',
		'setattr', 'slice', 'sorted', 'staticmethod', 'str', 'sum', 'super', 'tuple',
		'type', 'vars', 'zip', '__import__',

		# Magic constants and objects
		'__name__', '__file__', '__doc__', '__package__', '__loader__',
		'__spec__', '__build_class__', '__debug__',

		# Not built-in but often dangerous
		'exit', 'quit', 'copyright', 'credits', 'license'
	]


