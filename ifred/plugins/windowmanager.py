from idc import *

def handler(x):
	def f(self, item):
		self.window.close()
		return ProcessUiAction(x)
	return f

exports = {
	'Open: Functions': {
	'handler': handler('OpenFunctions')
	},
	'Open: Disassembly': {
	'handler': handler('OpenWindow')
	}
}