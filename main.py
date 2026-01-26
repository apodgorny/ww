import asyncio
import ww, yo

query  = 'what is the baking temperature'

asyncio.run(ww.tools.ExpertiseTool(
	query = query,
	top_k = 5,
))

print()
print('-' * 50)
print('QUERY:', query)
print('-' * 50)

yo.viz.ScoredText([
	(idx, score, texts[idx])
	for idx, score in scores
])



