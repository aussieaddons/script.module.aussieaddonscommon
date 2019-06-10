from __future__ import absolute_import, unicode_literals

import requests
import responses
import testtools

from aussieaddonscommon.exceptions import AussieAddonsException
from aussieaddonscommon.session import Session


class SessionTests(testtools.TestCase):

    @responses.activate
    def test_request(self):
        responses.add(responses.GET, 'http://foo.bar/api/1/foobar',
                      json={'error': 'not found'}, status=404)
        responses.add(responses.GET, 'http://foo.bar/api/2/foobar',
                      body=requests.exceptions.SSLError())
        responses.add(responses.POST, 'http://foo.bar/api/1/foobar',
                      json={'success': True}, status=200)
        s = Session()
        self.assertRaises(requests.exceptions.HTTPError, s.get,
                          'http://foo.bar/api/1/foobar')
        self.assertRaises(AussieAddonsException, s.get,
                          'http://foo.bar/api/2/foobar')
        self.assertIs(
            True, s.post('http://foo.bar/api/1/foobar').json().get('success'))
