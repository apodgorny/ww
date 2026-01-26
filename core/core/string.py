from __future__ import annotations

import re, unicodedata


class String:
	'''String utilities for formatting, normalization, and validation.'''

	# ANSI styles
	RESET         = '\033[0m'
	BOLD          = '\033[1m'
	ITALIC        = '\033[3m'
	UNDERLINE     = '\033[4m'
	STRIKETHROUGH = '\033[9m'

	# ANSI colors
	BLACK         = '\033[30m'
	RED           = '\033[31m'
	GREEN         = '\033[32m'
	YELLOW        = '\033[33m'
	BLUE          = '\033[34m'
	MAGENTA       = '\033[35m'
	CYAN          = '\033[36m'
	WHITE         = '\033[37m'

	GRAY          = '\033[90m'
	LIGHTRED      = '\033[91m'
	LIGHTGREEN    = '\033[92m'
	LIGHTYELLOW   = '\033[93m'
	LIGHTBLUE     = '\033[94m'
	LIGHTMAGENTA  = '\033[95m'
	LIGHTCYAN     = '\033[96m'
	LIGHTWHITE    = '\033[97m'
	LIGHTGRAY     = GRAY  # alias
	DARK_GRAY     = '\033[38;5;235m'

	@staticmethod
	def slugify(
		text          : str,
		transliterate : bool = False,
		separator     : str  = '-'
	) -> str:
		'''
		Convert string to a lowercase slug with a custom separator.
		Optionally transliterate to ASCII.
		'''
		if transliterate:
			text = unicodedata.normalize('NFKD', text)
			text = text.encode('ascii', 'ignore').decode('ascii')

		text = text.lower()
		text = re.sub(r'[^\w\s-]', '', text)
		text = re.sub(r'[\s_]+', separator, text)
		return text.strip(separator)

	@staticmethod
	def indent(text: str, prefix: str = '\t') -> str:
		'''Adds `prefix` at the beginning of every non-empty line.'''
		return '\n'.join(
			f'{prefix}{line}' if line.strip() else line
			for line in text.splitlines()
		)

	@staticmethod
	def unindent(text: str) -> str:
		'''Removes common leading whitespace from all lines.'''
		return re.sub(r'\n\s+', '\n', text).strip()

	@staticmethod
	def is_empty(s: str) -> bool:
		'''Checks if string is None or consists only of whitespace.'''
		return not s or s.strip() == ''

	@staticmethod
	def to_snake_case(name: str) -> str:
		'''Converts CamelCase or kebab-case to snake_case.'''
		import re
		name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
		return name.replace('-', '_')

	@staticmethod
	def snake_to_camel(name: str, capitalize=True) -> str:
		'''Converts snake_case to CamelCase or camelCase depending on `capitalize` argument value.'''
		components = name.split('_')
		if capitalize:
			return ''.join(x.title() for x in components)
		return components[0] + ''.join(x.title() for x in components[1:])

	@staticmethod
	def camel_to_snake(name: str) -> str:
		'''Converts CamelCase to snake_case (preserving acronyms).'''
		import re
		return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

	@staticmethod
	def normalize_whitespace(text: str) -> str:
		'''Replaces multiple spaces/newlines with a single space.'''
		import re
		return re.sub(r'\s+', ' ', text).strip()

	@staticmethod
	def underlined(text: str) -> str:
		'''Underlines the given text.'''
		return f'{String.UNDERLINE}{text}{String.RESET}'

	@staticmethod
	def italic(text: str) -> str:
		'''Italicizes the given text.'''
		return f'{String.ITALIC}{text}{String.RESET}'

	@staticmethod
	def strikethrough(text: str) -> str:
		'''Strikes through the given text.'''
		return f'{String.STRIKETHROUGH}{text}{String.RESET}'

	@staticmethod
	def color(text: str, color: str = None, styles: str = '') -> str:
		'''
		Wraps text in ANSI color and/or styles.
		'''
		parts = []

		if styles:
			if 'b' in styles : parts.append(String.BOLD)
			if 'u' in styles : parts.append(String.UNDERLINE)
			if 'i' in styles : parts.append(String.ITALIC)

		if color:
			parts.append(color)

		if not parts:
			return text  # No color, no style, return unchanged

		return f"{''.join(parts)}{text}{String.RESET}"


	@staticmethod
	def color_between(
		text      : str,
		begin     : str,
		end       : str,
		color     : str | None = None,
		styles    : str = '',
		inclusive : bool = True
	) -> str:
		'''
		Colorizes text between `begin` and `end` markers,
		with optional color and styles.
		'''
		if color is None and not styles:
			return text

		pat = re.compile(
			fr'({re.escape(begin)})(.*?)({re.escape(end)})',
			re.DOTALL
		)

		def repl(m: re.Match) -> str:
			left, middle, right = m.groups()
			if inclusive:
				# Красим маркеры + содержимое
				return String.color(f'{left}{middle}{right}', color, styles)
			else:
				# Красим только содержимое
				return f'{left}{String.color(middle, color, styles)}{right}'

		return pat.sub(repl, text)

	@staticmethod
	def highlight(text: str, highlight_groups: dict[tuple[str, str], list[str]]) -> str:
		'''
		Highlights words in text with specified (color, styles).

		highlight_groups format:
		{
			(String.LIGHTRED, 'b') : ['fox', 'jump'],
			(String.LIGHTGREEN, 'u') : ['dog', 'lazy'],
		}
		'''
		markers = []

		# Collect all markers manually
		for (color, styles), words in highlight_groups.items():
			for word in words:
				start = 0
				while True:
					pos = text.find(word, start)
					if pos == -1:
						break
					markers.append((pos, 'start', color, styles))
					markers.append((pos + len(word), 'end', color, styles))
					start = pos + len(word)

		# Sort markers: ends before starts if same position
		markers.sort(key=lambda x: (x[0], 0 if x[1] == 'end' else 1))

		# Build result
		result, active, last = [], [], 0
		for pos, kind, color, styles in markers:
			if last < pos:
				result.append(text[last:pos])

			if kind == 'start':
				active.append((color, styles))
				result.append(String.color('', color, styles)[:-len(String.RESET)])
			else:
				result.append(String.RESET)
				active.pop()
				if active:
					color, styles = active[-1]
					result.append(String.color('', color, styles)[:-len(String.RESET)])

			last = pos

		result.append(text[last:])
		if active:
			result.append(String.RESET)

		return ''.join(result)


