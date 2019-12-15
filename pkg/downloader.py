"""
HTTP downloader as minimal as possible.
I'm not sure if its codebase is minimal enough.
"""

import shutil
import tempfile

from .compat import (
    HTTPSConnection, HTTPConnection, urlparse,
    CannotSendRequest, ResponseNotReady, RemoteDisconnected)

# Supported protocols
SCHEME_MAP = {
    'https': HTTPSConnection,
    'http': HTTPConnection
}

# Default value of max retry count for one fetch
RETRY_COUNT = 3

# Keep-alive connections
CACHED_CONNECTIONS = {}


def _fetch(orig_url, timeout, retry=RETRY_COUNT):
    url = urlparse(orig_url)
    cls = SCHEME_MAP.get(url.scheme)

    if not retry:
        raise Exception("Max retries exceeded.")

    kwargs = {}
    if timeout is not None:
        kwargs['timeout'] = timeout

    key = (url.scheme, url.netloc)
    if key in CACHED_CONNECTIONS:
        conn = CACHED_CONNECTIONS[key]
    else:
        conn = cls(url.netloc, **kwargs)
        CACHED_CONNECTIONS[key] = conn
    try:
        conn.request(
            "GET",
            ''.join((url.path or '/', '?' + url.query if url.query else '')),
            headers={'Connection': 'Keep-Alive'})
    except (CannotSendRequest, OSError):  # Keep-alive expired
        del CACHED_CONNECTIONS[key]
        return _fetch(orig_url, timeout, retry)
    try:
        res = conn.getresponse()
    except (ResponseNotReady, RemoteDisconnected):
        # RemoteDisconnected is also triggered when keep-alive is disconnected
        # However it's safe to decrement retry count
        return _fetch(orig_url, timeout, retry - 1)

    loc = res.getheader("Location", None)
    if res.getheader("Connection", "").lower() == "close":
        del CACHED_CONNECTIONS[key]

    if res.status // 100 == 3 and loc:
        return _fetch(loc, timeout)

    return res


def download(url, timeout=None, to_file=False):
    res = _fetch(url, timeout)

    # Some interfaces like ZipFile need some additional methods.
    if to_file:
        out_file = tempfile.TemporaryFile()
        shutil.copyfileobj(res, out_file)
        out_file.seek(0)
        return out_file
    else:
        return res


if __name__ == '__main__':
    print(repr(download('http://idapkg.com', to_file=True).read()))
