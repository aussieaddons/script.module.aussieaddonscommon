from __future__ import absolute_import, unicode_literals

import io
import json

try:
    import mock
except ImportError:
    import unittest.mock as mock
import testtools
from future.moves.urllib.error import HTTPError, URLError
from future.moves.urllib.request import Request

from aussieaddonscommon import issue_reporter
from tests.unit import fakes

issue_reporter.GITHUB_API_TOKEN = 'abc123'


class IssueReporterTests(testtools.TestCase):

    def test_make_request(self):
        url = 'https://foo.bar'
        observed = issue_reporter.make_request(url)
        self.assertEqual(
            Request(url, headers=fakes.GITHUB_HEADERS).headers,
            observed.headers)
        self.assertEqual(
            Request(url, headers=fakes.GITHUB_HEADERS).get_full_url(),
            observed.get_full_url())

    @mock.patch('aussieaddonscommon.issue_reporter.urlopen')
    def test_get_connection_info(self, mock_urlopen):
        mock_urlopen.return_value = io.StringIO(
            json.dumps({'Foo': 'Bar'}, ensure_ascii=False))
        observed = issue_reporter.get_connection_info()
        self.assertEqual({'Foo': 'Bar'}, observed)

    @mock.patch('aussieaddonscommon.issue_reporter.io.open',
                mock.mock_open(read_data=fakes.KODI_LOG))
    @mock.patch('os.path.isfile')
    def test_get_kodi_log(self, mock_isfile):
        mock_isfile.return_value = True
        observed = issue_reporter.get_kodi_log()
        self.assertEqual(fakes.KODI_LOG_FILTERED, observed)

    def test_fetch_tags(self):
        observed = issue_reporter.fetch_tags(
            'aussieaddons/plugin.video.abc_iview')
        self.assertIn('v1.1.0', [x.get('name') for x in observed])

    @mock.patch('aussieaddonscommon.issue_reporter.fetch_tags')
    def test_get_versions(self, mock_tags):
        mock_tags.return_value = fakes.GITHUB_TAGS
        observed = issue_reporter.get_versions('')
        self.assertEqual(observed, fakes.GITHUB_VERSIONS)

    @mock.patch('aussieaddonscommon.issue_reporter.get_versions')
    def test_get_latest_version(self, mock_versions):
        mock_versions.return_value = fakes.GITHUB_VERSIONS
        latest = issue_reporter.get_latest_version('')
        self.assertEqual('1.8.5', latest)

    def test_is_not_latest_version(self):
        current = '1.8.5'
        latest = '1.9.0'
        self.assertIs(
            issue_reporter.is_not_latest_version(current, latest), True)
        current = '1.9.0'
        self.assertIs(
            issue_reporter.is_not_latest_version(current, latest), False)

    @mock.patch('aussieaddonscommon.issue_reporter.io.open',
                mock.mock_open(read_data=fakes.KODI_LOG))
    @mock.patch('aussieaddonscommon.utils.get_file_dir')
    @mock.patch('os.path.isfile')
    def test_not_already_reported(self, mock_isfile, mock_get_file_dir):
        mock_get_file_dir.return_value = ''
        mock_isfile.return_value = True
        observed = issue_reporter.not_already_reported(fakes.KODI_LOG)
        self.assertEqual(False, observed)
        observed = issue_reporter.not_already_reported(fakes.KODI_LOG_FILTERED)
        self.assertEqual(True, observed)

    @mock.patch('aussieaddonscommon.utils.get_file_dir')
    def test_save_last_error_report(self, mock_get_file_dir):
        mock_get_file_dir.return_value = '/'
        with mock.patch('aussieaddonscommon.issue_reporter.io.open',
                        mock.mock_open()) as mock_open:
            issue_reporter.save_last_error_report(fakes.KODI_LOG)
            handle = mock_open()
            handle.write.assert_any_call(fakes.KODI_LOG)

    @mock.patch('aussieaddonscommon.utils.get_file_dir')
    def test_save_last_error_report_read_bytes(self, mock_get_file_dir):
        mock_get_file_dir.return_value = '/'
        report = io.BytesIO(fakes.KODI_LOG.encode('utf-8'))
        with mock.patch('aussieaddonscommon.issue_reporter.io.open',
                        mock.mock_open()) as mock_open:
            issue_reporter.save_last_error_report(report.read())
            handle = mock_open()
            handle.write.assert_any_call(fakes.KODI_LOG.encode('utf-8'))

    @mock.patch('aussieaddonscommon.issue_reporter.urlopen')
    def test_get_org_repos(self, mock_urlopen):
        mock_urlopen.return_value = io.StringIO(
            json.dumps(fakes.GITHUB_REPOS_RAW, ensure_ascii=False))
        observed = issue_reporter.get_org_repos()
        self.assertEqual(fakes.GITHUB_REPOS, observed)

    @mock.patch('aussieaddonscommon.issue_reporter.get_org_repos')
    @mock.patch('aussieaddonscommon.utils.get_addon_id')
    def test_is_supported_addon(self, mock_addon_id, mock_repos):
        mock_repos.return_value = fakes.GITHUB_REPOS
        mock_addon_id.return_value = 'plugin.video.abc_iview'
        observed = issue_reporter.is_supported_addon()
        self.assertEqual(True, observed)
        mock_addon_id.return_value = 'plugin.video.plus7'
        observed = issue_reporter.is_supported_addon()
        self.assertEqual(None, observed)

    @mock.patch('aussieaddonscommon.issue_reporter.not_already_reported')
    def test_is_reportable(self, mock_not_reported):
        mock_not_reported.return_value = True
        observed = issue_reporter.is_reportable(fakes.FakeException,
                                                fakes.EXC_VALUE, fakes.TB)
        self.assertEqual(True, observed)

    def test_valid_country(self):
        info = fakes.VALID_CONNECTION_INFO[0]
        self.assertEqual(True, issue_reporter.valid_country(info))
        info = fakes.INVALID_CONNECTION_INFO[0]
        self.assertEqual(False, issue_reporter.valid_country(info))

    def test_blacklisted_hostname(self):
        info = fakes.VALID_CONNECTION_INFO[0]
        self.assertEqual(False, issue_reporter.blacklisted_hostname(info))
        info = fakes.INVALID_CONNECTION_INFO[1]
        self.assertEqual(True, issue_reporter.blacklisted_hostname(info))

    @mock.patch('sys.path')
    @mock.patch('aussieaddonscommon.utils.get_platform')
    @mock.patch('sys.platform', 'win32')
    @mock.patch('sys.version', '2.7.16')
    @mock.patch('aussieaddonscommon.utils.get_kodi_version')
    @mock.patch('xbmcaddon.Addon')
    @mock.patch('platform.uname')
    def test_generate_report(self, mock_uname, mock_addon, mock_kodi_version,
                             mock_get_platform, mock_sys_path):
        mock_uname.return_value = fakes.UNAME
        mock_addon.return_value = fakes.FakeAddon()
        mock_kodi_version.return_value = '18.2'
        mock_get_platform.return_value = 'Windows'
        mock_sys_path.return_value = 'C:\\Users\\user\\foo'
        with mock.patch('sys.argv', ['foo', 'bar', '?action=sendreport']):
            observed = issue_reporter.generate_report(
                'Foo', connection_info=fakes.VALID_CONNECTION_INFO[0])
        self.assertEqual(fakes.REPORT, observed)

    def test_upload_report(self):
        with mock.patch(
                'aussieaddonscommon.issue_reporter.urlopen') as mock_urlopen:
            mock_urlopen.return_value = io.StringIO(
                json.dumps({'html_url': 'http://foo.bar'}, ensure_ascii=False))
            observed = issue_reporter.upload_report(fakes.REPORT)
            self.assertEqual('http://foo.bar', observed)

        with mock.patch(
                'aussieaddonscommon.issue_reporter.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = URLError('invalid url')
            with mock.patch('aussieaddonscommon.utils.log') as mock_log:
                issue_reporter.upload_report(fakes.REPORT)
                self.assertRaises(URLError, issue_reporter.urlopen)
                mock_log.assert_called_once_with(
                    'Failed to report issue: URLError invalid url')

        with mock.patch(
                'aussieaddonscommon.issue_reporter.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = HTTPError(
                'http://foo.bar', '404', 'Not found', {},
                io.StringIO('Not Found'))
            with mock.patch('aussieaddonscommon.utils.log') as mock_log:
                issue_reporter.upload_report(fakes.REPORT)
                self.assertRaises(HTTPError, issue_reporter.urlopen)
                mock_log.assert_called_once_with(
                    'Failed to report issue: HTTPError 404\n Not Found')

    @mock.patch('aussieaddonscommon.issue_reporter.urlopen')
    def test_upload_report_ensure_bytes(self, mock_urlopen):
        issue_reporter.upload_report(fakes.REPORT)
        self.assertIsInstance(mock_urlopen.call_args.args[1], bytes)

    @mock.patch('aussieaddonscommon.issue_reporter.make_request')
    @mock.patch('aussieaddonscommon.issue_reporter.get_kodi_log')
    def test_upload_log(self, mock_get_log, mock_make_request):
        mock_get_log.return_value = fakes.KODI_LOG_FILTERED
        make_request_obj = issue_reporter.make_request(
            issue_reporter.GIST_API_URL)
        mock_make_request.return_value = make_request_obj
        with mock.patch(
                'aussieaddonscommon.issue_reporter.urlopen') as mock_urlopen:
            mock_urlopen.return_value = io.StringIO(
                json.dumps({'html_url': 'http://foo.bar'}, ensure_ascii=False))
            observed = issue_reporter.upload_log()
            mock_urlopen.assert_called_once_with(
                make_request_obj, json.dumps(fakes.LOG_DATA).encode('utf-8'))
            self.assertEqual('http://foo.bar', observed)

        with mock.patch(
                'aussieaddonscommon.issue_reporter.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = HTTPError(
                'http://foo.bar', '404', 'Not found', {},
                io.StringIO('Not Found'))
            with mock.patch('aussieaddonscommon.utils.log') as mock_log:
                issue_reporter.upload_log()
                mock_urlopen.assert_called_with(
                    issue_reporter.make_request(issue_reporter.GIST_API_URL),
                    json.dumps(fakes.LOG_DATA).encode('utf-8'))
                self.assertRaises(HTTPError, issue_reporter.urlopen)
                mock_log.assert_called_with(
                    'Failed to save log: HTTPError 404')

    @mock.patch('aussieaddonscommon.issue_reporter.generate_report')
    @mock.patch('aussieaddonscommon.issue_reporter.upload_log')
    def test_report_issue(self, mock_upload_log, mock_generate_report):
        mock_upload_log.return_value = 'http://foo.bar/log'
        mock_generate_report.return_value = fakes.REPORT
        with mock.patch(
                'aussieaddonscommon.issue_reporter.upload_report') as \
                mock_upload_report:
            mock_upload_report.return_value = 'http://foo.bar/report'
            observed = issue_reporter.report_issue('Foo')
            self.assertEqual('http://foo.bar/report', observed)
        with mock.patch(
                'aussieaddonscommon.issue_reporter.upload_report') as \
                mock_upload_report:
            mock_upload_report.side_effect = Exception()
            self.assertRaises(Exception, issue_reporter.report_issue, 'Foo')
