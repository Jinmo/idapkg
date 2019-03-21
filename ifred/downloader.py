import httplib
from Queue import Queue
from threading import Thread
from urlparse import urlparse


def __do_work(queue, callback):
    while not queue.empty():
        url = queue.get()
        status, url = __fetch(url)
        callback(status, url)
        queue.task_done()


def __fetch(orig_url):
    try:
        url = urlparse(orig_url)
        if url.scheme == 'https':
            conn = httplib.HTTPSConnection(url.netloc)
        elif url.scheme == 'http':
            conn = httplib.HTTPConnection(url.netloc)
        conn.request("GET", url.path)
        res = conn.getresponse()
        return res, orig_url
    except:
        return None, orig_url


def download_multi(urls, cb):
    concurrent = len(urls)
    q = Queue(concurrent * 2)
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
