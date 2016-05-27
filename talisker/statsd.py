from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
from builtins import *  # noqa

import os
from urllib.parse import urlparse, parse_qs
from statsd import StatsClient, defaults


_client = None


class TaliskerStatsdClient(StatsClient):
    def __init__(self,
                 host=defaults.HOST,
                 port=defaults.PORT,
                 prefix=defaults.PREFIX,
                 maxudpsize=defaults.MAXUDPSIZE,
                 ipv6=defaults.IPV6):

        # store ipv6 config or else it's buried in socket
        self.ipv6 = ipv6

        super(TaliskerStatsdClient, self).__init__(
            host, port, prefix, maxudpsize, ipv6)

    @property
    def port(self):
        return self._addr[1]

    @property
    def prefix(self):
        return self._prefix

    @property
    def hostport(self):
        return self.hostname + ':' + str(self.port)

    @property
    def maxudpsize(self):
        return self._maxudpsize


def get_config():
    client = get_client()
    if isinstance(client, DummyClient):
        return {}
    else:
        return {
            'host': client.hostname,
            'hostport': client.hostport,
            'port': client.port,
            'prefix': client.prefix,
            'maxudpsize': client.maxudpsize,
            'ipv6': client.ipv6,
        }


def parse_statsd_dsn(dsn):
    parsed = urlparse(dsn)
    host = parsed.hostname
    port = parsed.port or defaults.PORT
    prefix = None
    if parsed.path:
        prefix = parsed.path.strip('/').replace('/', '.')
    ipv6 = parsed.scheme in ('udp6', 'tcp6')
    size = int(
        parse_qs(parsed.query).get('maxudpsize', [defaults.MAXUDPSIZE])[0])
    return host, port, prefix, size, ipv6


def get_client(dsn=None):
    global _client

    if _client is None:
        if dsn is None:
            dsn = os.environ.get('STATSD_DSN', None)
        if dsn is None:
            _client = DummyClient()
        else:
            if not dsn.startswith('udp'):
                raise Exception('Talisker only supports udp stastd client')
            _client = TaliskerStatsdClient(*parse_statsd_dsn(dsn))

    return _client


class DummyClient(TaliskerStatsdClient):

    def _after(self, stat):
        pass
