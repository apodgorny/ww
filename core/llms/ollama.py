# ======================================================================
# Ollama model
# ======================================================================

import json, dirtyjson
import re

from ollama import AsyncClient

import ww


class Ollama(ww.base.Model):

	# ------------------------------------------------------------------
	def __init__(self, model_name, host = 'http://localhost:11434'):
		super().__init__(model_name)
		self.host = host

	# ------------------------------------------------------------------
	def _sanitize(self, text):

		text = text.replace('\n', '')
		text = re.sub(r'\\([^\\ntbr"\\/u])', r'\\\\\1', text)
		text = re.sub(r',\s*(null|None)\s*]', ']', text)
		text = re.sub(r',\s*]', ']', text)

		first = text.find('{')
		last  = text.rfind('}')

		if first != -1 and last != -1 and last > first:
			text = text[first:last+1]

		return text

	# ==================================================================
	# PROVIDER ENTRY
	# ==================================================================

	async def warmup(self):
		await AsyncClient(host=self.host).generate(
			model   = self.model_name,
			prompt  = ' ',
			options = {'keep_alive': -1}
		)

	async def generate_json(
		self,
		messages,
		schema,
		temperature,
		verbose
	):
		params = {
			'model'    : self.model_name,
			'messages' : messages,
			'format'   : schema,
			'options'  : {'temperature': temperature, 'keep_alive': 60}
		}

		client        = AsyncClient(host=self.host)
		full_content  = ''

		async for part in await client.chat(
			model    = self.model_name,
			messages = params['messages'],
			options  = params['options'],
			stream   = True,
		):
			chunk = part['message']['content']
			if self.verbose: print(chunk, end='', flush=True)
			full_content += chunk

		if self.verbose: print('\n' + '-' * 30)
		safe_content = self._sanitize(full_content)

		try:
			return json.loads(safe_content)
		except Exception:
			match = re.search(
				r'({.*?}|\[.*?\])',
				safe_content,
				re.DOTALL
			)
			if match:
				try:
					return dirtyjson.loads(match.group(1))
				except Exception as e2:
					self.print('‼️ JSON fallback parse error:', e2)

			self.print('‼️ Model output parse fail, RAW:\n', safe_content)

			raise ValueError('No valid JSON found in model output')
