import json, dirtyjson
import re
from ollama import AsyncClient
from wordwield.core import Model

class OllamaModel(Model):
	def __init__(self, name: str, host: str = 'http://localhost:11434'):
		self.name = name
		self.host = host

	def _sanitize(self, text: str) -> str:
		# BAD_QUOTES = '“”„«»‘’‚‹›'
		# text = ''.join('"' if c in BAD_QUOTES else c for c in text)
		text = text.replace('\n', '')
		text = re.sub(r'\\([^\\ntbr"\\/u])', r'\\\\\1', text)
		text = re.sub(r',\s*(null|None)\s*]', ']', text)
		text = re.sub(r',\s*]', ']', text)
		# Обрезать всё до первой {
		first = text.find('{')
		last  = text.rfind('}')
		if first != -1 and last != -1 and last > first:
			text = text[first:last+1]
		return text

	async def __call__(
		self,
		prompt          : str,
		response_schema : dict,
		role            : str        = 'user',
		temperature     : float      = 0.0,
		system          : str | None = None,
		verbose         : bool       = True
	) -> dict:
		params = {
			'model'    : self.name,
			'messages' : [{'role': role, 'content': prompt}],
			'format'   : response_schema,
			'options'  : {'temperature': temperature, 'keep_alive': 60}
		}
		if system:
			params['messages'].insert(0, {'role': 'system', 'content': system})

		if verbose:
			print(prompt)
			print('-' * 30)
			print(f'✅ {self.name} response:')

		client = AsyncClient(host=self.host)
		full_content = ''
		async for part in await client.chat(
			model    = self.name,
			messages = params['messages'],
			options  = params['options'],
			stream   = True,
		):
			chunk = part['message']['content']
			if verbose:
				print(chunk, end='', flush=True)
			full_content += chunk

		if verbose:
			print('\n' + '-' * 30)

		safe_content = self._sanitize(full_content)
		try:
			return json.loads(safe_content)
		except Exception as e:
			match = re.search(r'({.*?}|\[.*?\])', safe_content, re.DOTALL)
			if match:
				try:
					return dirtyjson.loads(match.group(1))
				except Exception as e2:
					if verbose:
						print('‼️ JSON fallback parse error:', e2)
			# Логируем полный ответ и падаем
			if verbose:
				print('‼️ Model output parse fail, RAW:\n', safe_content)
			raise ValueError('No valid JSON found in model output')
