import asyncio
import ww, yo, o


ww.Conf.PROJECT   = 'test'
ww.Conf.DB_PATH   = f'{ww.Conf.PROJECT}.db'
ww.Conf.EXPERTISE = ww.expertise

# o.Db.drop_all_tables()

domain = 'bread'
query  = 'what temperature do I bake the pizza'

result = asyncio.run(ww.tools.ExpertiseTool()(
	domain = domain,
	query  = query,
	top_k  = 5,
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



