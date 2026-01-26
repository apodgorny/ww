# ======================================================================
# Agent for semantic web search, ingestion, and retrieval.
# ======================================================================

import ww


class RagAgent(ww.base.Agent):
	intent   = 'Semantic expertise search and retrieval'  # Generic intent description
	verbose  = False                                      # Disable verbose output

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Perform semantic web search and return relevant chunks
	# ----------------------------------------------------------------------
	async def invoke(self,
		query     : str,  # User-provided search query or intent text
		top_k     : int,
		max_steps : int
	) -> list[str]:
		
		items = ww.services.ExpertiseService.search(
			query     = query,
			top_k     = top_k,
			max_steps = max_steps
		)
		return items
