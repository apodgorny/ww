from whitelabel.wl import WL

def initialize(ww, o, yo):
	o.Db.connect('sqlite:///db.sqlite3')
	o.Serializer
	yo.models.Encoder
	yo.models.Reranker

WL.define(
	'ww',
	__file__,
	import_libs = [
		'/Users/alexander/dev/yo/yo.py',
		'/Users/alexander/dev/o/o.py'
	],
	on_initialize = initialize
)
