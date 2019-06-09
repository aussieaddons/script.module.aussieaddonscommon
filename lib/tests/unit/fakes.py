# This Python file uses the following encoding: utf-8

# utils.py
class FakeAddon(object):
    def __init__(self, id='test.addon'):
        self.id = id
        self.name = 'Test Add-on'
        self.version = '0.0.1'

    def getSetting(self, id):
        return ''

    def setSetting(self, id, value):
        pass

    def openSettings(self):
        pass

    def getAddonInfo(self, key):
        return getattr(self, key)

#  fakes for tracebacks
#  https://stackoverflow.com/questions/19248784/faking-a-traceback-in-python

class FakeCode(object):
    def __init__(self, co_filename, co_name):
        self.co_filename = co_filename
        self.co_name = co_name


class FakeFrame(object):
    def __init__(self, f_code, f_globals):
        self.f_code = f_code
        self.f_globals = f_globals

class FakeTraceback(object):
    def __init__(self, frames, line_nums):
        if len(frames) != len(line_nums):
            raise ValueError("Ya messed up!")
        self._frames = frames
        self._line_nums = line_nums
        self.tb_frame = frames[0]
        self.tb_lineno = line_nums[0]

    @property
    def tb_next(self):
        if len(self._frames) > 1:
            return FakeTraceback(self._frames[1:], self._line_nums[1:])


class FakeException(Exception):
    def __init__(self, *args, **kwargs):
        self._tb = None
        super(Exception, self).__init__(*args, **kwargs)

    @property
    def __traceback__(self):
        return self._tb

    @__traceback__.setter
    def __traceback__(self, value):
        self._tb = value

    def with_traceback(self, value):
        self._tb = value
        return self


code1 = FakeCode("made_up_filename.py", "non_existent_function")
code2 = FakeCode("another_non_existent_file.py", "another_non_existent_method")
frame1 = FakeFrame(code1, {})
frame2 = FakeFrame(code2, {})
EXC_VALUE = FakeException('Another AFL 503 error')
TB = FakeTraceback([frame1, frame2], [1, 3])
EXC_FORMATTED_SUMMARY = "made_up_filename.py (1) - FakeException: " \
                        "Another AFL 503 error"
EXC_VALUE_FORMATTED = 'FakeException: Another AFL 503 error'

PLUGIN_URL_DICT = {
    'category': 'channel/abc1',
    'episode_count': '18',
    'series_url': 'programs/7-30/NC1901H086S00'
}

PLUGIN_URL_STRING = "?category=channel%2Fabc1&episode_count=18&series_url" \
                    "=programs%2F7-30%2FNC1901H086S00"

UNICODE_STRING_WITH_ACCENTS = u"Klüft skräms inför på fédéral électoral große"

EXC_INFO = (TypeError,)

BUILD_VERSION = '18.2 Git:20190422-f2643566d0'

ISSUE_URL = 'https://github.com/aussieaddons/issue-reports/issues/123'

VALID_CONNECTION_INFO = [
    {
        u'loc': u'-35.3066,149.1250', u'city': u'Capital Hill',
        u'ip': u'123.234.56.78',
        u'region': u'Australian Capital Territory',
        u'hostname': u'123-234-56-78.dyn.iinet.net.au',
        u'country': u'AU',
        u'org': u'AS4739 Internode Pty Ltd', u'postal': u'2600'
    }
]

INVALID_CONNECTION_INFO = [
    {
        u'loc': u'42.0707,-72.0440', u'city': u'Southbridge',
        u'ip': u'66.87.125.72',
        u'region': u'Massachusetts',
        u'hostname': u'66-87-125-72.pools.spcsdns.net',
        u'country': u'US',
        u'org': u'AS10507 Sprint Personal Communications Systems',
        u'postal': u'01550'
    },
    {
        u'loc': u'-33.9167,151.1830', u'city': u'Saint Peters',
        u'ip': u'137.59.252.166',
        u'region': u'New South Wales',
        u'hostname': u'137.59.252.166',
        u'country': u'AU',
        u'org': u'AS46562 Total Server Solutions L.L.C', u'postal': u'2015'
    },
    {
        u'loc': u'37.3422,-121.8830', u'city': u'San Jose',
        u'ip': u'216.151.183.137',
        u'region': u'California',
        u'hostname': u'216-151-183-137.ipvanish.com',
        u'country': u'US',
        u'org': u'AS33438 Highwinds Network Group, Inc.', u'postal': u'95112'
    },
    {
        u'loc': u'37.3422,-121.8830', u'city': u'Sydney',
        u'ip': u'209.107.195.97',
        u'region': u'New South Wales',
        u'hostname': u'209-107-195-97.ipvanish.com',
        u'country': u'AU',
        u'org': u'AS33438 Highwinds Network Group, Inc.', u'postal': u'2000'
    }
]

# issue_reporter.py

GITHUB_HEADERS = {
    "Authorization": "token abc123",
    "Content-Type": "application/json",
}

KODI_LOG = """
NOTICE: Using Release Kodi x64 build
Accessing https://user123:password1@example.com
<user>user123</user>
<pass>password1</pass>
"""

KODI_LOG_FILTERED = """
NOTICE: Using Release Kodi x64 build
Accessing https://[FILTERED_USER]:[FILTERED_PASSWORD]@example.com
<user>[FILTERED_USER]</user>
<pass>[FILTERED_PASSWORD]</pass>
"""

GITHUB_TAGS = [
    {
        u'commit': {
            u'url':
                u'https://api.github.com/repos/aussieaddons/plugin.video'
                u'.abc_iview/commits/7686d42e4d877776bbbf2501d01dec7365071533',
            u'sha':
                u'7686d42e4d877776bbbf2501d01dec7365071533'},
        u'zipball_url':
            u'https://api.github.com/repos/aussieaddons/plugin.video'
            u'.abc_iview/zipball/v1.8.5',
        u'tarball_url':
            u'https://api.github.com/repos/aussieaddons/plugin.video'
            u'.abc_iview/tarball/v1.8.5',
        u'name': u'v1.8.5',
        u'node_id': u'MDM6UmVmNDMwOTMxNDp2MS44LjU='}, {
        u'commit': {
            u'url':
                u'https://api.github.com/repos/aussieaddons/plugin.video'
                u'.abc_iview/commits/01b9f3852c78b7d64eabb91c8872090e3dd9200c',
            u'sha':
                u'01b9f3852c78b7d64eabb91c8872090e3dd9200c'},
        u'zipball_url':
            u'https://api.github.com/repos/aussieaddons/plugin.video'
            u'.abc_iview/zipball/v1.8.4',
        u'tarball_url':
            u'https://api.github.com/repos/aussieaddons/plugin.video'
            u'.abc_iview/tarball/v1.8.4',
        u'name': u'v1.8.4',
        u'node_id': u'MDM6UmVmNDMwOTMxNDp2MS44LjQ='
    }
]

GITHUB_VERSIONS = [
    '1.8.5',
    '1.8.4'
]

GITHUB_REPOS_RAW = [
    {
        u'description': u'Kodi add-on for AFL Video',
        u'name': u'plugin.video.afl-video',
        u'language': u'Python'
    },
    {
        u'description': u'Aussie Add-ons repository for Kodi',
        u'name': u'repo',
        u'language': u'Python'
    },
    {
        u'description': u'ABC iView add-on for Kodi',
        u'name': u'plugin.video.abc_iview',
        u'language': u'Python'
    },
    {
        u'description': u'Tools for XBMC Addon management',
        u'name': u'tools',
        u'language': u'Python'
    },
    {
        u'description': u'ABC News 24 Live Stream Plugin for XBMC',
        u'name': u'plugin.video.live.au.abc_news24',
        u'language': u'Python'
    },
    {
        u'description': u'GitHub Issue Reporter Module for XBMC Addons',
        u'name': u'script.module.githubissuereporter',
        u'language': u'Python'
    }
]

GITHUB_REPOS = [
    u'plugin.video.afl-video', u'repo', u'plugin.video.abc_iview', u'tools',
    u'plugin.video.live.au.abc_news24', u'script.module.githubissuereporter']

UNAME = ('Windows', 'Home-Office', '10', '10.0.17763', 'AMD64',
         'AMD64 Family 23 Model 1 Stepping 1, AuthenticAMD')

REPORT = {
    'body': u'*Automatic bug report from end-user.*\n\n## '
            u'Environment\n\n**Add-on Name:** Test Add-on\n**Add-on ID:** '
            u'test.addon\n**Add-on Version:** 0.0.1\n**Add-on URL:** '
            u'?action=sendreport\n**Kodi Version:** 18.2\n**Python '
            u'Version:** 2.7.16\n**IP Address:** '
            u'123.234.56.78\n**Hostname:** '
            u'123-234-56-78.dyn.iinet.net.au\n**Country:** AU\n**ISP:** '
            u'AS4739 Internode Pty Ltd\n**Operating System:** win32  ('
            u'Windows 10 AMD64)\n**Platform:** Windows\n**Python Path:**\n```\n\n```',
    'title': '[addon] Foo'}

LOG_DATA = {
    "files": {
        "kodi.log": {
            "content": KODI_LOG_FILTERED
        }
    }
}
