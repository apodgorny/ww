# ======================================================================
# Agent for semantic web search, ingestion, and retrieval.
# ======================================================================

import ww


class ExpertiseTool(ww.base.Tool):
	intent   = 'Semantic expertise search and retrieval'  # Generic intent description
	verbose  = False                                      # Disable verbose output

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Perform semantic web search and return relevant chunks
	# ----------------------------------------------------------------------
	async def invoke(self,
		domain    : str,
		query     : str,
		top_k     : int
	) -> list[str]:
		
		items = ww.services.Expertise.search(
			domain_key = domain,
			query      = query,
			top_k      = top_k
		)
		return items
