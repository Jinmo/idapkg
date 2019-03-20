import traceback
import json

from .package import InstallablePackage
from ..downloader import download_multi
from StringIO import StringIO

from ..config import g


def get_online_packages(repos=None):
    if repos is None:
        repos = g['repos']

    results = []

    def collector(res, repo_url):
        try:
            if res is None:
                raise Exception('connection error')
            r = json.load(res)
            base = r['base']
            assert isinstance(r['packages'], list)
            results.append((InstallablePackage(
                name=item['name'], path=item['path'], version=item['version'], base=base) for item in r['packages']))
        except:
            io = StringIO()
            traceback.print_exc(file=io)
            print 'Error fetching repo: %r\n%s' % (repo_url, io.getvalue())

    download_multi(repos, collector)

    result = []
    for generator in results:
        for item in generator:
            result.append(item)

    return result


if __name__ == '__main__':
    for x in get_online_packages():
        print x
