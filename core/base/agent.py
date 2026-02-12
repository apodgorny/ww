# ======================================================================
# ======================================================================
# Base class for all LLM-driven agents.
# ======================================================================

from __future__ import annotations

import inspect
from typing import Any

from jinja2 import Environment, BaseLoader

import ww


class Agent(ww.base.Operator):
	ResponseSchema  : Any  = None                       # Output schema for LLM response
	intent          : str  = None                       # Semantic role in project
	template        : str  = None                       # Jinja prompt template
	verbose         : bool = True                       # Verbose LLM output flag

	# Initialize agent instance and registries
	# ----------------------------------------------------------------------
	def __init__(self, name=None):
		super().__init__(name=name)                      # Initialize operator base
		Registry('state', self)                          # Register state registry
		self._register_agents()                          # Register nested agents
		self._register_streams()                         # Register streams

	# Execute agent call lifecycle
	# ----------------------------------------------------------------------
	async def __call__(self, *args, **kwargs):
		signature = inspect.signature(self.invoke)       # Inspect invoke signature
		arg_names = [param.name for param in signature.parameters.values()]

		n = 0
		for n in range(min(len(args), len(arg_names))):
			kwargs[arg_names[n]] = args[n]               # Map positional args to kwargs

		args = args[n+1:]                                # Remaining args

		self.to_state(*args, **kwargs)                   # Populate state
		await self.init()                                # Agent-specific init
		await self._collect_props()                      # Collect properties into state
		return await self.invoke(*args, **kwargs)        # Execute main logic

	# ======================================================================
	# PRIVATE METHODS
	# ======================================================================

	# Register nested agent instances
	# ----------------------------------------------------------------------
	def _register_agents(self):
		if hasattr(self.__class__, 'agents'):
			agent_dict = dict(self.agents)                # Copy agent declarations
			delattr(self.__class__, 'agents')             # Remove class-level declaration
			Registry('agents', self)                      # Register agent registry

			for agent_name, agent_class in agent_dict.items():
				agent                   = agent_class(agent_name)
				agent.owner             = self
				agent.state['owner']    = self
				self.agents[agent_name] = agent

	# Register agent streams
	# ----------------------------------------------------------------------
	def _register_streams(self):
		if hasattr(self.__class__, 'streams'):
			stream_list = list(self.streams)              # Copy stream declarations
			delattr(self.__class__, 'streams')            # Remove class-level declaration
			Registry('streams', self)                     # Register stream registry

			for stream_name in stream_list:
				full_stream_name = f'{self.__class__.ns}.{self.name}__{stream_name}'.replace(
					'operators.', ''
				)
				stream = o.T.StreamSchema.put(
					name   = full_stream_name,
					role   = stream_name,
					author = self.name
				)
				self.streams[stream_name] = stream

	# Collect properties and atomic values into state
	# ----------------------------------------------------------------------
	async def _collect_props(self, state=None):
		state = state or self.state
		for name in dir(self.__class__):
			if not name.startswith('__'):
				prop = getattr(self.__class__, name)
				if isinstance(prop, property):
					prop = getattr(self, name)
					state[name] = await prop if inspect.isawaitable(prop) else prop
				elif is_atomic(prop):
					state[name] = prop

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Store objects and keyword values into state
	# ----------------------------------------------------------------------
	def to_state(self, *args, **kwargs):
		for obj in args:
			if hasattr(obj, 'to_dict'):
				obj = obj.to_dict()                      # Convert O instance to dict
			if isinstance(obj, dict):
				self.state.update(obj)                   # Merge dict into state
			else:
				raise ValueError(
					f'Object `{str(obj)[:20]}...` of type {type(obj)} '
					f'must have associated key to be stored in state of `{self.name}`'
				)
		self.state.update(kwargs)                        # Merge keyword args

	# Render prompt template with current state
	# ----------------------------------------------------------------------
	async def fill(self, template: str = None, **vars) -> str:
		await self._collect_props()                      # Refresh state properties

		template = template or self.template
		if not template:
			raise RuntimeError(f'Template is not defined in `{self.name}`')

		try:
			template  = String.unindent(template)
			all_vars  = {**self.state.to_dict(), **vars, 'ww': ww}
			env       = Environment(loader=BaseLoader())
			env.globals = {'len': len}
			jinja     = env.from_string(template)
			prompt    = String.unindent(jinja.render(**all_vars))
		except Exception as e:
			raise ValueError(
				f'Could not fill template in agent `{self.name}`: {str(e)}'
			)

		return prompt

	# Query LLM using filled prompt and response schema
	# ----------------------------------------------------------------------
	async def ask(self, prompt=None, schema=None, unpack=True, verbose=None, **extra_fields):
		verbose     = self.verbose if verbose is None else verbose
		prompt      = prompt or await self.fill()
		schema      = schema or self.ResponseSchema
		instruction = (
			'\n\nPut all data into JSON, output JSON ONLY. '
			'Wrap strings in quotes, make sure JSON is valid:\n'
		)

		if schema is None:
			raise RuntimeError(f'No ResponseSchema is defined in agent `{self.name}`')

		llm_schema, non_llm_schema = schema.split('llm')
		prompt                    += instruction + llm_schema.to_schema_prompt()

		self.log(f'\n========================[ 😎 AGENT `{self.name}` ]========================\n')

		partial = await ww.ask(
			prompt  = prompt,
			schema  = llm_schema,
			verbose = verbose
		)

		full = schema(**{**partial, **extra_fields})
		self.to_state(full)                              # Store response in state
		return full.unpack() if unpack else full.to_dict()


	# ======================================================================
	# Hooks
	# ======================================================================

	# Optional agent initialization hook
	# ----------------------------------------------------------------------
	async def init(self):
		pass

	# Optional agent write hook
	# ----------------------------------------------------------------------
	async def write(self):
		pass

	# Default invoke implementation
	# ----------------------------------------------------------------------
	async def invoke(self, *args, **kwargs):
		unpack = kwargs.pop('unpack') if 'unpack' in kwargs else True
		prompt = await self.fill(self.template)
		result = await self.ask(
			prompt  = prompt,
			schema  = self.ResponseSchema,
			unpack  = unpack,
			verbose = self.verbose
		)
		print(result, type(result))
		await self.write()
		return result
