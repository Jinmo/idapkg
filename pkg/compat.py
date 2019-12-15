import sys

if sys.version_info.major == 3:
    from http.client import (
        HTTPSConnection, HTTPConnection, CannotSendRequest, ResponseNotReady, RemoteDisconnected)
    from urllib.parse import urlparse, quote

    basestring = str
else:
    from urllib import quote
    from urlparse import urlparse
    from httplib import (
        HTTPSConnection, HTTPConnection, CannotSendRequest, ResponseNotReady, BadStatusLine as RemoteDisconnected)

    basestring = basestring
