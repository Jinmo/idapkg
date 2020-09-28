import sys

if sys.version_info.major == 3:
    from http.client import (
        HTTPSConnection, HTTPConnection, CannotSendRequest, ResponseNotReady, RemoteDisconnected)
    from urllib.parse import urlparse, urljoin, quote

    basestring = str
else:
    from urllib import quote
    from urlparse import urlparse, urljoin
    from httplib import (
        HTTPSConnection, HTTPConnection, CannotSendRequest, ResponseNotReady, BadStatusLine as RemoteDisconnected)

    basestring = basestring

__all__ = (
    'quote', 'urlparse',
    'HTTPSConnection', 'HTTPConnection', 'CannotSendRequest', 'ResponseNotReady', 'RemoteDisconnected',
    'basestring')
