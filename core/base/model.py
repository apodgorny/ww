# ======================================================================
# Model base class
# ======================================================================

import ww


class Model(ww.Module):

	# ------------------------------------------------------------------
	def __init__(self, model_name):
		self.model_name = model_name

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	async def generate(
		self,
		prompt,
		schema,
		system      = None,
		temperature = 0.0,
		verbose     = True
	):

		self.verbose = verbose
		if self.verbose: print(f'\n========================[ 😎 ]========================\n')

		system_prompt = self._get_system_prompt(system, schema)

		messages = [
			{'role': 'system', 'content': system_prompt},
			{'role': 'user',   'content': prompt}
		]

		print(f'{"-"*50}\nUSER PROMPT:\n{"-"*50}\n{prompt}')
		print(f'{"-"*50}\nSYSTEM PROMPT:\n{"-"*50}\n{system_prompt}')

		if self.verbose: print(f'\n=====================[ {self.model_name} ]=====================')
		
		response = await self.generate_json(
			messages    = messages,
			schema      = schema,
			temperature = temperature,
			verbose     = verbose
		)

		print(response)

		return response

	# ======================================================================
	# PRIVATE METHODS
	# ======================================================================

	def _get_system_prompt(self, system, schema):
		default_prompt = (
			'Return ONLY strict valid JSON.\n'
			'Skip explanations.\n'
			'Skip markdown.\n'
			'Skip extra text.\n'
			'Fill the following JSON template with values:\n'
		)
		default_prompt += schema.to_prompt()

		return default_prompt if system is None else system

	# ------------------------------------------------------------------

	async def _generate_json(self, messages, schema, temperature, verbose):
		raise NotImplementedError('Provider must implement `_generate_json`')
