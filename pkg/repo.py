import json
import traceback
from StringIO import StringIO

from .package import InstallablePackage, LocalPackage
from .config import g
from .downloader import download_multi

TIMEOUT = 8


def get_online_packages(repos=None):
    """
    Generates a list of packages from specified repositories.

    :param repos: Array of url strings pointing valid repos. Default: g['repos']
    """
    if repos is None:
        repos = g['repos']

    results = []
    endpoint = '/plugins'

    def collector(res, repo_url):
        repo_url = repo_url[:-len(endpoint)]
        try:
            if res is None:
                raise Exception('connection error')
            r = json.load(res)
            assert isinstance(r['data'], list)
            results.append((InstallablePackage(
                name=item['name'], id=item['id'], version=item['version'], repo=repo_url)
                for item in r['data'] if LocalPackage.by_name(item['id']) is None))
        except:
            io = StringIO()
            traceback.print_exc(file=io)
            logger.error('Error fetching repo: %r\n%s' %
                         (repo_url, io.getvalue()))

    download_multi([x + endpoint for x in repos], collector, timeout=TIMEOUT)

    result = []
    for generator in results:
        for item in generator:
            result.append(item)

    return result


if __name__ == '__main__':
    for x in get_online_packages():
        print x
