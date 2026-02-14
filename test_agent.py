import asyncio
import ww, yo, o


ww.Conf.PROJECT = 'test'
ww.Conf.DB_PATH = f'{ww.Conf.PROJECT}.db'

# o.Db.drop_all_tables()

query = 'what are the main steps to bake sourdough bread'

async def main():
	return await ww.agents.Test(
		3, 5, 7
	)


result = asyncio.run(main())