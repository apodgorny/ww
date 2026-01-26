import sys

from white_label import WhiteLabel

class WW(WhiteLabel):
	foo = 'bar'

WW.imp('/Users/alexander/dev/yo/yo.py')
WW()
