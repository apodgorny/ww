from .string import String


class Highlight:

	@staticmethod
	def python(s):
		s = String.highlight(s, {
			(String.CYAN, '')    : 'async def self return await class float int str bool'.split(),
			(String.GRAY, '')    : '{ } [ ] : = - + * /, . ; \" \''.split(),
			(String.MAGENTA, '') : '( )'.split()
		})
		s = String.color_between(s, '#', '\n', String.GRAY, styles='i')
		return s