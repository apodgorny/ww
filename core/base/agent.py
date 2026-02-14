import inspect

from jinja2 import Environment, DictLoader

import ww, o


class Agent(ww.base.Operator):

	# Query LLM using filled prompt and response schema
	# ----------------------------------------------------------------------
	async def __call__(self, verbose=True):
		return await ww.llms.Ollama('gemma3:4b').generate(
			prompt  = await self._fill(),
			schema  = self.ResponseSchema,
			verbose = verbose
		)

	# ----------------------------------------------------------------------
	async def __invoke__(self, *args, **kwargs):
		self.ctx       = ww.Registry()
		self.ctx.input = ww.Registry()
		self.ctx.self  = ww.Registry()

		await self.initialize()

		if not hasattr(self, 'ResponseSchema') : raise RuntimeError(f'`{self.__ww_module__}.ResponseSchema` is not defined')
		if not hasattr(self, 'template')       : raise RuntimeError(f'`{self.__ww_module__}.template` is not defined')

		self._collect_input(*args, **kwargs)

		return await self.invoke(*args, **kwargs)

	# ======================================================================
	# PRIVATE METHODS
	# ======================================================================

	# ----------------------------------------------------------------------
	def _make_env(self):
		templates = {}
		name_map  = {}

		# Register sub-templates
		for name in dir(self.__class__):
			if name.startswith('template_'):
				source = getattr(self.__class__, name)
				if isinstance(source, str):
					key            = f'{name}.j2'
					templates[key] = ww.String.unindent(source)
					name_map[name] = key

		loader             = DictLoader(templates)
		env                = Environment(loader=loader)
		env.globals['len'] = len

		# Replace ctx.self template_* with registered names
		for name, key in name_map.items():
			self.ctx.self[name] = key

		return env

	# ----------------------------------------------------------------------
	# def _collect_input(self, *args, **kwargs):
	# 	signature = inspect.signature(self.invoke)
	# 	try:
	# 		bound = signature.bind(*args, **kwargs)
	# 	except TypeError as e:
	# 		raise TypeError(f'{self.__ww_module__}(): {e}')

	# 	bound.apply_defaults()
	# 	self.ctx.input.update(bound.arguments)

	def _collect_input(self, *args, **kwargs):
		signature = inspect.signature(self.invoke)

		try:
			bound = signature.bind(*args, **kwargs)
		except TypeError as e:
			raise TypeError(f'{self.__ww_module__}(): {e}')

		bound.apply_defaults()

		for name, param in signature.parameters.items():

			if param.kind == inspect.Parameter.VAR_POSITIONAL:
				values = bound.arguments.get(name, ())
				for i, value in enumerate(values):
					self.ctx.input[str(i)] = value

			elif param.kind == inspect.Parameter.VAR_KEYWORD:
				values = bound.arguments.get(name, {})
				for key, value in values.items():
					self.ctx.input[key] = value

			else:
				if name in bound.arguments:
					self.ctx.input[name] = bound.arguments[name]

	# ----------------------------------------------------------------------
	async def _collect_props(self):
		for name in dir(self.__class__):
			if not name.startswith('__'):
				prop = getattr(self.__class__, name)
				if isinstance(prop, property):
					prop = getattr(self, name)
					self.ctx.self[name] = await prop if inspect.isawaitable(prop) else prop
				elif o.Type(prop).is_atomic():
					self.ctx.self[name] = prop

	# ----------------------------------------------------------------------
	async def _fill(self, template=None):
		await self._collect_props() # Get fresh values

		template = template or self.template

		try:
			template = ww.String.unindent(template)
			env      = self._make_env()
			jinja    = env.from_string(template)
			prompt   = ww.String.unindent(jinja.render(ctx=self.ctx))
		except Exception as e:
			raise ValueError(
				f'Template fill failed in `{self.__ww_module__}`: {str(e)}'
			)

		return prompt

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	async def initialize(self): pass

	async def invoke(self, *args, **kwargs):
		raise NotImplementedError('Operator must implement invoke method')


