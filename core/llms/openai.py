# ======================================================================
# OpenAI model
# ======================================================================

import json
import asyncio

from openai import OpenAI

from wordwield.core import Model


class OpenaiModel(Model):

	# ------------------------------------------------------------------
	def __init__(self, model_name = 'gpt-4o'):
		super().__init__(model_name)
		self.client = OpenAI()

	# ------------------------------------------------------------------
	def _to_json_schema(self, schema):
		schema                         = schema.to_json_schema()
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

	# ==================================================================
	# PROVIDER ENTRY
	# ==================================================================

	async def generate_json(
		self,
		messages,
		schema,
		temperature,
		verbose
	):

		params = {
			'model'           : self.model_name,
			'temperature'     : temperature,
			'response_format' : self._to_json_schema(schema),
			'messages'        : messages
		}

		try:
			response = await asyncio.to_thread(
				self.client.chat.completions.create,
				**params
			)
			result = json.loads(
				response.choices[0].message.content
			)

		except json.JSONDecodeError as e:
			raise ValueError(
				f'OpenaiModel JSON parsing error: {e}'
			)

		except Exception as e:
			raise ValueError(
				f'OpenaiModel LLM communication error: {e}'
			)

		return result
