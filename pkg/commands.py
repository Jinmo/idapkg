# Some console-friendly functions

from pkg.package import InstallablePackage
import threading

def __work(f):
	t = threading.Thread(target=f)
	t.start()
	return t

def install(spec, repo):
	return __work(lambda: InstallablePackage.install_from_url(spec, repo + spec))
