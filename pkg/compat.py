import sys

if sys.version_info.major == 3:
    from queue import Queue
    from http.client import (
        HTTPSConnection, HTTPConnection, CannotSendRequest, ResponseNotReady)
    from urllib.parse import urlparse, quote

    basestring = str
else:
    from httplib import (
        HTTPSConnection, HTTPConnection, CannotSendRequest, ResponseNotReady)
    from Queue import Queue
    from urllib import quote
    from urlparse import urlparse

    basestring = basestring
