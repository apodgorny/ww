# ======================================================================
# WebSearchTool
# ======================================================================

import ww


class WebSearchTool(ww.base.Tool):

	intent  = 'Semantic web search and retrieval'
	verbose = False

	# ----------------------------------------------------------------------
	async def invoke(self,
		query     : str,
		k_results : int = 5,
		k_chunks  : int = 10,
	):
		return await ww.services.WebSearch.search(
			query      = query,
			k_results  = k_results,
			k_chunks   = k_chunks
		)
