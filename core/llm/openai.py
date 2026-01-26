import json
import asyncio
from openai import OpenAI

from wordwield.core import Model


class OpenaiModel(Model):
	def __init__(self, name='gpt-4o'):
		super().__init__(name)
		self.client = OpenAI()

	def to_json_schema(self, schema):
		schema                         = super().to_json_schema(schema)
		schema_name                    = f'{self.__class__.__name__.lower()}_response_schema'
		schema['type']                 = 'object'
		schema['additionalProperties'] = False

		return {
			'type'        : 'json_schema',
			'json_schema' : {
				'name'   : schema_name,
				'schema' : schema
			}
		}

	async def __call__(
		self,
		prompt          : str,
		response_schema : type,
		role            : str = 'user',
		temperature     : float = 0.0,
		system          : str | None = None
	) -> dict:
		messages = []
		if system:
			messages.append({'role': 'system', 'content': system})
		messages.append({'role': role, 'content': prompt})

		params = {
			'model'           : self.name,
			'temperature'     : temperature,
			'response_format' : self.to_json_schema(response_schema),
			'messages'        : messages
		}

		try:
			response = await asyncio.to_thread(
				self.client.chat.completions.create,
				**params
			)
			return json.loads(response.choices[0].message.content)
		except json.JSONDecodeError as e:
			raise ValueError(f'OpenAIModel JSON parsing error: {e}')
		except Exception as e:
			raise ValueError(f'OpenAIModel LLM communication error: {e}')
		