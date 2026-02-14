import ww, o


class Test(ww.base.Agent):

	ResponseSchema = o.T.define(
		answer = o.F(int, 'Result of calculation')
	)

	template = '''
		Calculate sum of following numbers
		{% for key, value in ctx.input.items() %}
			{% include ctx.self.template_1 %}
		{% endfor %}
	'''

	template_1 = '''
		{{ value }}
	'''

	async def invoke(self, *args):
		return await self()

