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

    def get(self, name):
        """
        Fetch metadata for single package from the repo.

        :returns: None if package is not found,
          else a :class:`~pkg.package.InstallablePackage` object
        :rtype: pkg.package.InstallablePackage or None
        """
        raise NotImplementedError

    def list(self):
        """
        Fetch a list of all packages in the repo.

        :returns: list of InstallablePackage in the repo.
        :rtype: list(pkg.package.InstallablePackage)
        """
        raise NotImplementedError

    def releases(self, name):
        """
        Fetch a list of releases of specified package.
        """
        raise NotImplementedError

    @staticmethod
    def from_url(url):
        def old_repo(name):
            return OldRepository(name)

        def github_repo(name):
            assert name.startswith('github:')
            return GitHubRepository(name[7:])

        supported_types = {
            'https': old_repo,
            'http': old_repo,
            'github': github_repo
        }

        return supported_types[url.split(':')[0]](url)

    def __repr__(self):
        raise NotImplementedError


class OldRepository(Repository):
    """
    S3-hosted repository.
    https://github.com/Jinmo/idapkg-api
    """

    def __init__(self, url, timeout=TIMEOUT):
        self.url = url
        self.timeout = timeout

    def get(self, name):
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
        endpoint = '/releases?name=' + quote(name)
        res = download(self.url + endpoint)

        if res is None:
            return None

        releases = json.load(res)
        if not releases['success']:
            raise Exception("Server returned error")
        else:
            return releases['data']

    def download(self, name, version):
        endpoint = '/download?spec=' + quote(name) + '==' + quote(version)
        return download(self.url + endpoint, to_file=True)

    def __repr__(self):
        return "<OldRepository url=%r>" % self.url


class GitHubRepository(Repository):
    """
    GitHub-hosted repository.
    https://github.com/Jinmo/idapkg-repo
    """
    API_BLOB = 'https://raw.githubusercontent.com/{0}/{1}'
    API_ARCHIVE = 'https://github.com/{0}/archive/{1}.zip'

    def __init__(self, repo, timeout=TIMEOUT):
        assert self._is_valid_repo(repo)
        self.repo = repo
        self.timeout = timeout

    def get(self, name):
        endpoint = 'info/{0}.json'.format(quote(name))
        res = download(self.API_BLOB.format(self.repo, endpoint))
        item = json.load(res)
        return InstallablePackage(
            name=item['name'], id=item['id'], version=item['version'], description=item['description'],
            author=item['author'], repo=self)

    def list(self):
        res = download(self.API_BLOB.format(self.repo, '/list.json'))
        items = json.load(res)
        return [
            InstallablePackage(
                name=item['name'], id=item['id'], version=item['version'], description=item['description'],
                author=item['author'], repo=self)
            for item in items
        ]

    def releases(self, name):
        endpoint = 'releases/{0}.json'.format(quote(name))
        res = download(self.API_BLOB.format(self.repo, endpoint))
        return json.load(res)

    def download(self, name, version):
        endpoint = 'releases/{0}.json'.format(quote(name))
        releases = json.load(download(self.API_BLOB.format(self.repo, endpoint)))
        for release in releases:
            if release['version'] == version:
                repo = release['repo']
                commit = release['commit']
                assert self._is_valid_repo(repo)
                assert self._is_valid_commit(commit)
                return download(self.API_ARCHIVE.format(repo, commit), to_file=True)

        raise Exception("release not found! (%s==%s)" % (name, version))

    @staticmethod
    def _is_valid_repo(repo):
        if repo.count('/') not in (1, 2):
            return False

        if repo.count('/') == 1:
            repo += '/master'

        if '..' in repo:
            return False

        owner, name, branch_or_commit = repo.split('/')

        if '.' in (owner, name, branch_or_commit):
            return False

        # From https://github.com/join:
        # Username may only contain alphanumeric characters or single hyphens, and
        # cannot begin or end with a hyphen.
        if not all('a' <= x <= 'z' or x == '-' for x in owner.lower()):
            return False

        if not owner or owner[0] == '-' or owner[-1] == '-':
            return False

        # Guesses from https://github.com/new
        if not all('a' <= x <= 'z' or x in '.-_' for x in name.lower()):
            return False

        # Basic names only
        if not all('a' <= x <= 'z' or x in '.-_' for x in branch_or_commit.lower()):
            return False

        return True

    @staticmethod
    def _is_valid_commit(commit):
        return len(commit) == 40 and all(x in '0123456789abcdef' for x in commit)

    def __repr__(self):
        return "<GitHubRepository repo=%r>" % self.repo


def get_online_packages(repos=None):
    """
    Generates a list of packages from specified repositories.

    :param repos: Array of repository urls (string). Default: g['repos']
    :type repos: list(str) or None
    :returns: list(:class:`~pkg.package.InstallablePackage`) from each repos.
    """

    if repos is None:
        repos = g['repos']

    repos = [Repository.from_url(url) for url in repos]

    pool = ThreadPool(MAX_CONCURRENT)
    results = pool.map(lambda repo: repo.list(), repos)
    results = [pkgs for pkgs in results if pkgs]

    # flatten results
    return [pkg for pkgs in results for pkg in pkgs]


if __name__ == '__main__':
    print('\n'.join(map(repr, get_online_packages(['github:Jinmo/idapkg-repo/master']))))
