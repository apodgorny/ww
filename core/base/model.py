import os, re

from pydantic import BaseModel

from wordwield.core.module import Module
from wordwield.core.string import String
from wordwield.core.o      import O
from wordwield.core.t      import T


class Model:

	##################################################################

	@classmethod
	def load(cls, model_id, models_registry):
		if '::' not in model_id:
			raise ValueError(f'Invalid model_id: `{model_id}`. Expected format `provider::name`')

		provider, model_name = model_id.split('::', 1)
		model_key            = f'{String.snake_to_camel(provider)}Model'
		model_class          = models_registry[model_key]
		model                = model_class(model_name)
		model.model_id       = model_id

		return model
	
	@classmethod
	def restart(cls):
		if hasattr(cls, 'model'):
			cls.model.restart_model()
		
	##################################################################

	@classmethod
	def validate(cls, data: dict, schema: O):
		'''
		Filters out extra fields from data and returns an instance of schema,
		filling with schema defaults for missing fields.
		'''
		field_names   = set(schema.model_fields.keys())
		data_filtered = {k: v for k, v in data.items() if k in field_names}
		default       = schema.to_default().to_dict()
		default.update(data_filtered)
		schema(**default)
		return default

	@classmethod
	async def generate(
		cls,
		ww,
		
		prompt          : str,
		response_schema : O,

		model_id        : str,
		role            : str        = 'user',
		temperature     : float      = 0.0,
		system          : str | None = None,
		verbose         : bool       = True

	) -> dict:
		if not issubclass(response_schema, O):
			raise ValueError(f'Model.generate requires `response_model` to be a subclass of `O`, but received `{type(response_schema)}`')

		cls.model  = Model.load(model_id, ww.models)
		result = await cls.model(
			prompt          = prompt,
			response_schema = response_schema.to_jsonschema(),
			role            = role,
			temperature     = temperature,
			system          = system,
			verbose         = verbose
		)
		return cls.validate(result, response_schema)
		
	def restart_model(self):
		pass
