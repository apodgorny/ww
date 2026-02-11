# ======================================================================
# Base class for deterministic execution tools.
# ======================================================================

import ww, yo


class Tool(ww.base.Operator):

	# Initialize tool instance
	# ----------------------------------------------------------------------
	def __init__(self, name=None):
		super().__init__(name=name)                      # Initialize operator base
		self.state = yo.struct.D()

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Execute deterministic tool logic
	# ----------------------------------------------------------------------
	async def invoke(self, *args, **kwargs):
		raise NotImplementedError(
			f'Tool `{self.__class__.__name__}` must implement invoke method'
		)
