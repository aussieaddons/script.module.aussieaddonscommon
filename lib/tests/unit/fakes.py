# This Python file uses the following encoding: utf-8

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


class FakeCode(object):
    def __init__(self, co_filename, co_name):
        self.co_filename = co_filename
        self.co_name = co_name

#  fakes for tracebacks
#  https://stackoverflow.com/questions/19248784/faking-a-traceback-in-python
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
TB = FakeTraceback([frame1, frame2], [1,3])
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


EXC_INFO = (TypeError, )

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

# Some systems we support
SYSTEMS = [
    # Linux
    {
        'system': 'Linux',
        'platforms': ['System.Platform.Linux'],
        'machine': 'x86_64',
        'expected_system': 'Linux',
        'expected_arch': 'x64',
    },
    # Generic Windows
    {
        'system': 'Windows',
        'platforms': ['System.Platform.Windows'],
        'machine': 'AMD64',
        'arch': '32bit',
        'expected_system': 'Windows',
        'expected_arch': 'x86',
    },
    # Generic Mac OS X
    {
        'system': 'Darwin',
        'platforms': ['System.Platform.OSX'],
        'machine': 'x86_64',
        'expected_system': 'Darwin',
        'expected_arch': 'x64',
    },
    # Raspberry Pi
    {
        'system': 'Linux',
        'platforms': ['System.Platform.Linux.RaspberryPi',
                      'System.Platform.Linux'],
        'machine': 'armv7l',
        'expected_system': 'Linux',
        'expected_arch': 'arm',
    },
    # Nexus Player/MiBox
    {
        'system': 'Linux',
        'platforms': ['System.Platform.Android',
                      'System.Platform.Linux'],
        'machine': 'arm',
        'expected_system': 'Android',
        'expected_arch': 'arm',
    },
    # Windows (UWP)
    {
        'system': 'Windows',
        'platforms': ['System.Platform.Windows',
                      'System.Platform.UWP'],
        'machine': '',
        'arch': '64bit',
        'expected_system': 'UWP',
        'expected_arch': 'x64',
    },
    # Xbox One
    {
        'system': 'Windows',
        'platforms': ['System.Platform.Windows',
                      'System.Platform.UWP'],
        'machine': '',
        'arch': '64bit',
        'expected_system': 'UWP',
        'expected_arch': 'x64',
    },
]


ARCHES = [
    ('aarch64', 'aarch64'),
    ('aarch64_be', 'aarch64'),
    ('arm64', 'aarch64'),
    ('arm', 'arm'),
    ('armv7l', 'arm'),
    ('armv8', 'aarch64'),
    ('AMD64', 'x64'),
    ('x86_64', 'x64'),
    ('x86', 'x86'),
    ('i386', 'x86'),
    ('i686', 'x86'),
]

KODI_BUILDS = [
    {
        'build': '13.2 Git:Unknown',
        'version': '13.2',
        'major_version': 13,
        'build_name': 'Gotham',
        'build_date': None,
    },
    {
        'build': '17.6 Git:20180213-nogitfound',
        'version': '17.6',
        'major_version': 17,
        'build_name': 'Krypton',
        'build_date': '20180213',
    },
    {
        'build': '17.6 Git:20171119-ced5097',
        'version': '17.6',
        'major_version': 17,
        'build_name': 'Krypton',
        'build_date': '20171119',
    },
    {
        'build': '18.0-ALPHA1 Git:20180225-02cb21ec7d',
        'version': '18.0',
        'major_version': 18,
        'build_name': 'Leia',
        'build_date': '20180225',
    },
]


# Expected output from calling Addons.GetAddonDetails for IA if not installed
IA_NOT_AVAILABLE = {
    'id': 1,
    'jsonrpc': '2.0',
    'error': {
        'message': 'Invalid params.',
        'code': -32602
    }
}

IA_ENABLED = {
    'id': 1,
    'jsonrpc': u'2.0',
    'result': {
        'addon': {
            'addonid': 'inputstream.adaptive',
            'enabled': True,
            'type': 'kodi.inputstream'
        }
    }
}

TRANS_PATH_ARGS = [
    "addon.getSetting('DECRYPTERPATH')",
    'special://xbmcbinaddons/inputstream.adaptive',
    'special://home/'
]

TRANSLATED_PATHS = {
    'Linux': ['/storage/.kodi/cdm',
              '/storage/.kodi/addons/inputstream.adaptive'],
    'Windows': ['C:/Users/user/AppData/Roaming/Kodi/cdm',
                'C:/Program Files (x86)/Kodi/addons/inputstream.adaptive'],
    'Darwin': ['/Users/User/Library/Application Support/Kodi/cdm/']
}
