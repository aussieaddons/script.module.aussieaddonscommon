from __future__ import absolute_import, unicode_literals
from future.utils import string_types
import json

try:
    import mock
except ImportError:
    import unittest.mock as mock

import testtools
import traceback
import xbmc

from future.moves.urllib.parse import parse_qsl
from tests.unit import fakes
from aussieaddonscommon import utils


def get_xbmc_cond_visibility(cond):
    if cond == 'System.Platform.Linux':
        return True
    else:
        return False


class UtilsTests(testtools.TestCase):

    @mock.patch('xbmcaddon.Addon', fakes.FakeAddon)
    def test_get_addon_id(self):
        addon_id = utils.get_addon_id()
        self.assertEqual('test.addon', addon_id)

    @mock.patch('xbmcaddon.Addon', fakes.FakeAddon)
    def test_get_addon_name(self):
        addon_name = utils.get_addon_name()
        self.assertEqual('Test Add-on', addon_name)

    @mock.patch('xbmcaddon.Addon', fakes.FakeAddon)
    def test_get_addon_version(self):
        addon_version = utils.get_addon_version()
        self.assertEqual('0.0.1', addon_version)

    def test_descape(self):
        self.assertEqual('<spam&eggs>', utils.descape('&lt;spam&amp;eggs&gt;'))

    def test_get_url(self):
        url = fakes.PLUGIN_URL_STRING
        expected = fakes.PLUGIN_URL_DICT
        self.assertEqual(expected, utils.get_url(url))

    def test_make_url(self):
        url = fakes.PLUGIN_URL_DICT
        self.assertEqual(url, dict(parse_qsl(utils.make_url(url))))

    def test_ensure_ascii(self):
        string = fakes.UNICODE_STRING_WITH_ACCENTS
        expected = 'Kluft skrams infor pa federal electoral groe'
        self.assertEqual(expected, utils.ensure_ascii(string))
        self.assertIsInstance(utils.ensure_ascii(string), string_types)

    @mock.patch('xbmcaddon.Addon', fakes.FakeAddon)
    @mock.patch('os.mkdir')
    @mock.patch('xbmc.translatePath')
    def test_get_file_dir(self, mock_translate_path, make_dir):
        mock_translate_path.return_value = '/home/kodi/.kodi/temp'
        observed = utils.get_file_dir().replace('\\', '/')
        self.assertEqual('/home/kodi/.kodi/temp/test.addon', observed)

    @mock.patch('xbmcaddon.Addon', fakes.FakeAddon)
    @mock.patch('xbmc.log')
    def test_log(self, mock_log):
        utils.log('foo')
        mock_log.assert_called_once_with(
            '[Test Add-on v0.0.1] foo', level=xbmc.LOGNOTICE)

    @mock.patch('xbmcaddon.Addon', fakes.FakeAddon)
    @mock.patch('sys.exc_info')
    def test_format_error_summary(self, mock_exc_info):
        mock_exc_info.return_value = (
            fakes.FakeException, fakes.EXC_VALUE, fakes.TB)
        self.assertEqual(fakes.EXC_FORMATTED_SUMMARY,
                         utils.format_error_summary())

    @mock.patch('xbmcaddon.Addon', fakes.FakeAddon)
    @mock.patch('sys.exc_info')
    @mock.patch('traceback.print_exc')
    @mock.patch('xbmc.log')
    def test_log_error(self, mock_log, mock_traceback, mock_exc_info):
        mock_exc_info.return_value = (
            fakes.FakeException, fakes.EXC_VALUE, fakes.TB)
        mock_traceback.return_value = 'foo'
        utils.log_error()
        mock_log.assert_any_call('[Test Add-on v0.0.1] ERROR: {0}'.format(
            fakes.EXC_FORMATTED_SUMMARY), level=xbmc.LOGERROR)
        mock_log.assert_called_with('foo', level=xbmc.LOGERROR)

    def test_dialog_message(self):
        observed = utils.format_dialog_message('bar a b\nc', 'foo')
        self.assertEqual(['foo', 'bar a b', 'c'], observed)

    @mock.patch('xbmcaddon.Addon', fakes.FakeAddon)
    @mock.patch('sys.exc_info')
    def test_format_dialog_error(self, mock_exc_info):
        mock_exc_info.return_value = (
            fakes.FakeException, fakes.EXC_VALUE, fakes.TB)
        observed = utils.format_dialog_error('Foo')
        self.assertEqual(
            ['Test Add-on v0.0.1 ERROR', fakes.EXC_FORMATTED_SUMMARY],
            observed)

    @mock.patch('xbmcgui.Dialog.ok')
    def test_dialog_message(self, mock_ok_dialog):
        utils.dialog_message('bar', 'foo')
        mock_ok_dialog.assert_called_once_with('foo', 'bar')

    @mock.patch('xbmc.getCondVisibility')
    def test_get_platform(self, mock_getCondVisibility):
        mock_getCondVisibility.side_effect = get_xbmc_cond_visibility
        platform = utils.get_platform()
        self.assertEqual('Linux', platform)

    @mock.patch('xbmc.getInfoLabel')
    def test_get_kodi_build(self, mock_info_label):
        mock_info_label.return_value = fakes.BUILD_VERSION
        self.assertEqual(fakes.BUILD_VERSION, utils.get_kodi_build())

    @mock.patch('xbmc.getInfoLabel')
    def test_get_kodi_version(self, mock_info_label):
        mock_info_label.return_value = fakes.BUILD_VERSION
        self.assertEqual('18.2', utils.get_kodi_version())

    @mock.patch('xbmc.getInfoLabel')
    def test_get_kodi_version_none(self, mock_info_label):
        mock_info_label.return_value = None
        self.assertEqual('0', utils.get_kodi_version())

    @mock.patch('xbmc.getInfoLabel')
    def test_get_kodi_major_version(self, mock_info_label):
        mock_info_label.return_value = fakes.BUILD_VERSION
        self.assertEqual(18, utils.get_kodi_major_version())

    @mock.patch('xbmc.getInfoLabel')
    def test_get_kodi_major_version_blank(self, mock_info_label):
        mock_info_label.return_value = ''
        self.assertEqual(0, utils.get_kodi_major_version())

    @mock.patch('xbmcaddon.Addon', fakes.FakeAddon)
    @mock.patch('xbmc.log')
    @mock.patch('xbmc.getCondVisibility')
    @mock.patch('xbmc.getInfoLabel')
    def test_log_kodi_platform_version(self, mock_info_label,
                                       mock_getCondVisibility,
                                       mock_log):
        mock_info_label.return_value = fakes.BUILD_VERSION
        mock_getCondVisibility.side_effect = get_xbmc_cond_visibility
        utils.log_kodi_platform_version()
        mock_log.assert_called_once_with(
            '[Test Add-on v0.0.1] Kodi 18.2 running on Linux',
            level=xbmc.LOGNOTICE)

    @mock.patch('aussieaddonscommon.utils.get_addon_version')
    def test_is_valid_version(self, mock_version):
        for ver in ['1.2.3', '0.0.1', '10.1.2-3~abcdef0']:
            mock_version.return_value = ver
            observed = utils.is_valid_version()
            self.assertEqual(True, observed)
        mock_version.return_value = '1001.1.3-2-abcdef0'
        observed = utils.is_valid_version()
        self.assertEqual(False, observed)

    def test_is_valid_country(self):
        for connection_info in fakes.VALID_CONNECTION_INFO:
            observed = utils.is_valid_country(connection_info)
            self.assertEqual(True, observed)
        for connection_info in fakes.INVALID_CONNECTION_INFO:
            observed = utils.is_valid_country(connection_info)
            self.assertEqual(False, observed)

    @mock.patch('xbmc.executeJSONRPC')
    def test_is_debug(self, mock_execute_json_rpc):
        mock_execute_json_rpc.return_value = json.dumps(
            {'result': {'value': True}})
        self.assertEqual(True, utils.is_debug())

    @mock.patch('aussieaddonscommon.utils.send_report')
    @mock.patch('aussieaddonscommon.issue_reporter.get_connection_info')
    @mock.patch('aussieaddonscommon.utils.is_debug')
    def test_user_report(self, mock_is_debug, mock_connection_info,
                         mock_send_report):
        mock_is_debug.return_value = True
        mock_connection_info.return_value = fakes.VALID_CONNECTION_INFO[0]
        utils.user_report()
        mock_send_report.assert_called_once_with(
            'User initiated report',
            connection_info=fakes.VALID_CONNECTION_INFO[0])

    @mock.patch('aussieaddonscommon.issue_reporter.report_issue')
    @mock.patch('aussieaddonscommon.issue_reporter.is_supported_addon')
    def test_send_report(self, mock_supported, mock_report_issue):
        mock_supported.return_value = True
        mock_report_issue.return_value = fakes.ISSUE_URL
        observed = utils.send_report(
            'Foo', trace=None, connection_info=fakes.VALID_CONNECTION_INFO[0])
        self.assertEqual(fakes.ISSUE_URL, observed)

    @mock.patch('xbmcaddon.Addon', fakes.FakeAddon)
    @mock.patch('aussieaddonscommon.issue_reporter.save_last_error_report')
    @mock.patch('aussieaddonscommon.utils.send_report')
    @mock.patch('xbmcgui.Dialog.yesno')
    @mock.patch('aussieaddonscommon.issue_reporter.get_latest_version')
    @mock.patch('aussieaddonscommon.issue_reporter.not_already_reported')
    @mock.patch('aussieaddonscommon.issue_reporter.get_connection_info')
    @mock.patch('aussieaddonscommon.utils.format_dialog_error')
    @mock.patch('traceback.format_exc')
    @mock.patch('sys.exc_info')
    def test_handle_error(self, mock_exc_info, mock_traceback,
                          mock_format_dialog_error, mock_connection_info,
                          mock_not_already_reported, mock_get_latest_version,
                          mock_yesno_dialog, mock_send_report,
                          mock_save_last_report):
        mock_exc_info.return_value = (
            fakes.FakeException, fakes.EXC_VALUE, fakes.TB)
        mock_traceback.return_value = ''.join(
            traceback.format_exception(fakes.FakeException, fakes.EXC_VALUE,
                                       fakes.TB))
        mock_format_dialog_error.return_value = ['Test Add-on v0.0.1 ERROR',
                                                 fakes.EXC_FORMATTED_SUMMARY]
        mock_connection_info.return_value = fakes.VALID_CONNECTION_INFO[0]
        mock_not_already_reported.return_value = True
        mock_get_latest_version.return_value = '0.0.1'
        mock_yesno_dialog.return_value = True
        utils.handle_error('Big error')
        mock_send_report.assert_called_once_with(
            fakes.EXC_VALUE_FORMATTED, trace=''.join(
                traceback.format_exception(fakes.FakeException,
                                           fakes.EXC_VALUE, fakes.TB)),
            connection_info=fakes.VALID_CONNECTION_INFO[0])
        mock_save_last_report.assert_called_once_with(
            fakes.EXC_VALUE_FORMATTED)
