import httplib
from Queue import Queue
from threading import Thread
from urlparse import urlparse

SCHEME_MAP = {
    'https': httplib.HTTPSConnection,
    'http': httplib.HTTPConnection
}

MAX_CONCURRENT = 10


def __do_work(queue, callback):
    while not queue.empty():
        url = queue.get()
        try:
            status, url = __fetch(url)
            callback(status, url)
        except:
            callback(None, url)
        finally:
            queue.task_done()


def __fetch(orig_url):
    url = urlparse(orig_url)
    cls = SCHEME_MAP.get(url.scheme)

    conn = cls(url.netloc)
    conn.request("GET", url.path)
    res = conn.getresponse()

    return res, orig_url


def download_multi(urls, cb):
    concurrent = min(len(urls), MAX_CONCURRENT)
    q = Queue(concurrent)
    for url in urls:
        q.put(url)
    for i in range(concurrent):
        t = Thread(target=__do_work, args=(q, cb,))
        t.daemon = True
        t.start()
    q.join()


def download(url):
    results = [None]

    def set_res(res, url):
        results[0] = res

    download_multi([url], set_res)
    return results[0]
