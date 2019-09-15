try:
	import __palette__
	from . import packagemanager
except ImportError:
	# actions are currently supported on ifred only.
	pass
