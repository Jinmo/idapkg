from __future__ import print_function

import json
import traceback
from multiprocessing.pool import ThreadPool

from .compat import quote
from .config import g
from .downloader import download
from .logger import getLogger
from .package import InstallablePackage

# Connection timeout
TIMEOUT = 8

# Max concurrent when fetching multiple repository
MAX_CONCURRENT = 10

log = getLogger(__name__)


class Repository(object):
    """
    An instance of this class represents a single repository.
    """

    def __init__(self, url, timeout=TIMEOUT):
        self.url = url
        self.timeout = timeout

    def get(self, name):
        """
        Fetch metadata for single package from the repo.

        :returns: None if package is not found,
          else a :class:`~pkg.package.InstallablePackage` object
        :rtype: pkg.package.InstallablePackage or None
        """
        endpoint = '/info?id=' + quote(name)
        res = download(self.url + endpoint, self.timeout)
        if not res:  # Network Error
            return

        res = json.load(res)
        if not res['success']:
            return
        else:
            item = res['data']
            return InstallablePackage(
                name=item['name'], id=item['id'], version=item['version'], description=item['description'],
                author=item['author'], repo=self)

    def list(self):
        """
        Fetch a list of all packages in the repo.

        :returns: list of InstallablePackage in the repo.
        :rtype: list(pkg.package.InstallablePackage)
        """
        endpoint = '/search'
        res = download(self.url + endpoint, self.timeout)
        try:
            if res is None:
                raise Exception('connection error')

            res = json.load(res)
            assert isinstance(res['data'], list)

            return [
                InstallablePackage(
                    name=item['name'], id=item['id'], version=item['version'], description=item['description'],
                    author=item['author'], repo=self)
                for item in res['data']
            ]
        except ValueError:
            log.error('Error fetching repo: %r\n%s',
                      self.url, traceback.format_exc())

    def releases(self, name):
        """
        Fetch a list of releases of specified package.
        """
        endpoint = '/releases?name=' + quote(name)
        res = download(self.url + endpoint)

        if res is None:
            return None

        releases = res.read()
        try:
            releases = json.loads(releases)
            if not releases['success']:
                log.debug("Server returned error")
                return None
            else:
                return releases['data']
        except (KeyError, ValueError):
            return None

    def download(self, name, version):
        endpoint = '/download?spec=' + quote(name) + '==' + quote(version)
        return download(self.url + endpoint, to_file=True)

    @staticmethod
    def from_urls(repos=None):
        if repos is None:
            repos = g['repos']

        return [Repository(repo) for repo in repos]

    def __repr__(self):
        return "<Repository url=%r>" % self.url


def get_online_packages(repos=None):
    """
    Generates a list of packages from specified repositories.

    :param repos: Array of repository urls (string). Default: g['repos']
    :type repos: list(str) or None
    :returns: list(:class:`~pkg.package.InstallablePackage`) from each repos.
    """

    repos = Repository.from_urls(repos)

    pool = ThreadPool(MAX_CONCURRENT)
    results = pool.map(lambda repo: repo.list(), repos)
    results = [pkgs for pkgs in results if pkgs]

    # flatten results
    return [pkg for pkgs in results for pkg in pkgs]


if __name__ == '__main__':
    print('\n'.join(map(repr, get_online_packages())))
