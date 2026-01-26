# ======================================================================
# Agent for semantic web search, ingestion, and retrieval.
# ======================================================================

import ww


class WebSearchTool(ww.base.Tool):
	intent   = 'Semantic web search and retrieval'     # Generic intent description
	verbose  = False                                   # Disable verbose output

	# ======================================================================
	# PUBLIC METHODS
	# ======================================================================

	# Perform semantic web search and return relevant chunks
	# ----------------------------------------------------------------------
	async def invoke(self,
		query            : str,                      # User-provided search query or intent text
		k_results        : int              = 5,     # Amount of results to consider
		k_chunks         : int              = 10,    # Amount of relevant chunks from results
		time_range       : tuple[int, int]  = None   # (from_ts, to_ts) unix timestamps
	) -> list[str]:
		
		relevant_chunks = await ww.services.WebSearchService.search(
			query      = query,
			k_results  = k_results,
			k_chunks   = k_chunks,
			time_range = time_range
		)

		return relevant_chunks
