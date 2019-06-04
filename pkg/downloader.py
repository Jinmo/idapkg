import httplib
from Queue import Queue
from threading import Thread
from urlparse import urlparse

SCHEME_MAP = {
    'https': httplib.HTTPSConnection,
    'http': httplib.HTTPConnection
}

MAX_CONCURRENT = 10


def __do_work(queue, callback, timeout):
    while not queue.empty():
        url = queue.get()
        if url is None:
            break
        try:
            status, url = __fetch(url, timeout)
            callback(status, url)
        except:
            callback(None, url)
        finally:
            queue.task_done()


def __fetch(orig_url, timeout):
    url = urlparse(orig_url)
    cls = SCHEME_MAP.get(url.scheme)

    kwargs = {}
    if timeout is not None:
        kwargs['timeout'] = timeout

    conn = cls(url.netloc, **kwargs)
    conn.request("GET", url.path + '?' + url.query)
    res = conn.getresponse()

    loc = res.getheader("Location", None)

    if res.status / 100 == 3 and loc:
        return __fetch(loc, timeout)

    return res, orig_url


def _download_multi(urls, cb, timeout=None):
    concurrent = min(len(urls), MAX_CONCURRENT)
    q = Queue(concurrent)

    for url in urls:
        q.put(url)

    for i in range(concurrent):
        __do_work(q, cb, timeout)


def _download(url, timeout=None):
    results = [None]

    def set_res(res, _url):
        results[0] = res

    _download_multi([url], set_res, timeout)
    return results[0]

if __name__ == '__main__':
    t = Thread(target=lambda: _download('https://idapkg.com'))
    t.start()
