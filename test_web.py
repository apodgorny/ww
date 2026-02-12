import asyncio
import ww, yo, o


ww.Conf.PROJECT = 'test'
ww.Conf.DB_PATH = f'{ww.Conf.PROJECT}.db'

# o.Db.drop_all_tables()

query = 'what are the main steps to bake sourdough bread'

result = asyncio.run(ww.tools.WebSearchTool()(
	query     = query,
	k_results = 3,
	k_chunks  = 5,
))

print()
print('=' * 80)
print('QUERY:', query)
print('=' * 80)

for document, items in result.items():
	print('Document:', document)
	print('-' * 80)
	yo.viz.ScoredText(items)
	print()
