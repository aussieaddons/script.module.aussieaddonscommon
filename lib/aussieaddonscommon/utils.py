import json
import os
import re
import sys
import traceback
import unicodedata

# This import is to deal with a python bug with strptime:
#   ImportError: Failed to import _strptime because the import lockis
#   held by another thread.
import _strptime  # noqa: F401

from future.moves.html.entities import entitydefs
from future.moves.urllib.parse import quote_plus, unquote_plus
from future.utils import iteritems, text_type

import xbmc

import xbmcaddon

import xbmcgui

# Used for fetching latest version information about the add-on
GITHUB_ORG = 'aussieaddons'

# HTML code escape
PATTERN = re.compile(r"&(\w+?);")


def get_addon():
    return xbmcaddon.Addon()


def get_addon_id():
    """Helper function for returning the version of the running add-on"""
    return get_addon().getAddonInfo('id')


def get_addon_name():
    """Helper function for returning the version of the running add-on"""
    return get_addon().getAddonInfo('name')


def get_addon_version():
    """Helper function for returning the version of the running add-on"""
    return get_addon().getAddonInfo('version')


def descape_entity(m, defs=entitydefs):
    """Translate one entity to its ISO Latin value"""
    try:
        return defs[m.group(1)]
    except KeyError:
        return m.group(0)  # use as is


def descape(string):
    """Translate html chars and ensure ascii"""
    string = ensure_ascii(string)
    string = PATTERN.sub(descape_entity, string)
    return string


def get_url(s):
    """Build a dict from a given Kodi add-on URL"""
    dict = {}
    pairs = s.lstrip("?").split("&")
    for pair in pairs:
        if len(pair) < 3:
            continue
        kv = pair.split("=", 1)
        k = kv[0]
        v = unquote_plus(kv[1])
        dict[k] = v
    return dict


def make_url(d):
    """Build a URL suitable for a Kodi add-on from a dict"""
    pairs = []
    for k, v in iteritems(d):
        k = quote_plus(k)
        v = ensure_ascii(v)
        v = quote_plus(v)
        pairs.append("%s=%s" % (k, v))
    return "&".join(pairs)


def ensure_ascii(s):
    """Force a string to acsii

    This is especially useful for Kodi menu items which will barf if given
    anything other than ascii
    """
    if sys.version_info >= (3, 0):
        return unicodedata.normalize('NFD', s).encode('ascii',
                                                      'ignore').decode('utf-8')
    if not isinstance(s, text_type):
        s = str(s)
        s = s.decode("utf-8")
    return unicodedata.normalize('NFD', s).encode('ascii', 'ignore')


def get_file_dir():
    """Get our add-on working directory

    Make our add-on working directory if it doesn't exist and
    return it.
    """
    filedir = os.path.join(
        xbmc.translatePath('special://temp/'), get_addon_id())
    if not os.path.isdir(filedir):
        os.mkdir(filedir)
    return filedir


def log(s):
    """Logging helper"""
    xbmc.log("[%s v%s] %s" % (get_addon_name(), get_addon_version(),
                              ensure_ascii(s)), level=xbmc.LOGINFO)


def append_message(msg_list, msg):
    """
    Add message with newline to existing formatted msg
    :param msg_list: list - contains title and content
    :param msg: message to append to content
    """
    assert len(msg_list) == 2
    msg_list[1] = '{0}\n{1}'.format(msg_list[1], msg)


def format_error_summary():
    """Format error summary

    From the traceback, generate a nicely formatted string showing the
    error message.
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()

    args = exc_value.args

    if exc_type == UnicodeEncodeError:
        args.pop(1)  # remove error data, likely to be very long xml
    return "%s (%d) - %s: %s" % (
        os.path.basename(exc_traceback.tb_frame.f_code.co_filename),
        exc_traceback.tb_lineno, exc_type.__name__,
        ', '.join([ensure_ascii(x) for x in args]))


def log_error(message=None):
    """Logging helper for exceptions"""
    try:
        xbmc.log("[%s v%s] ERROR: %s" %
                 (get_addon_name(), get_addon_version(),
                  format_error_summary()), level=xbmc.LOGERROR)
        xbmc.log(traceback.print_exc(), level=xbmc.LOGERROR)
    except Exception:
        pass


def format_dialog_message(msg, title=None):
    """Format a message suitable for a Kodi dialog box

    Valid input for msg is either a string (supporting newline chars) or a
    list of lines, with an optional title.
    """
    if title:
        content = [title]
    else:
        content = ["%s v%s" % (get_addon_name(), get_addon_version())]

    content.append(ensure_ascii(msg))
    return content


def format_dialog_error(msg=None):
    """Format an error message suitable for a Kodi dialog box"""
    title = "%s v%s ERROR" % (get_addon_name(), get_addon_version())
    error = format_error_summary()
    return format_dialog_message(error, title=title)


def dialog_message(msg, title=None):
    """Helper function for a simple 'OK' dialog"""
    content = format_dialog_message(msg, title)
    xbmcgui.Dialog().ok(*content)


def get_platform():
    """Get platform

    Work through a list of possible platform types and return the first
    match. Ordering of items is important as some match more than one type.

    E.g. Android will match both Android and Linux
    """
    platforms = [
        "Android",
        "Linux.RaspberryPi",
        "Linux",
        "UWP",
        "Windows",
        "ATV2",
        "IOS",
        "OSX",
        "Darwin",
    ]

    for platform in platforms:
        if xbmc.getCondVisibility('System.Platform.' + platform):
            return platform
    return "Unknown"


def get_kodi_build():
    """Return the Kodi build version"""
    try:
        return xbmc.getInfoLabel("System.BuildVersion")
    except Exception:
        return None


def get_kodi_version():
    """Return the version number of Kodi"""
    build = get_kodi_build()
    if build:
        version = build.split(' ')[0]
        return version
    else:
        return '0'


def get_kodi_major_version():
    """Return the major version number of Kodi"""
    version = get_kodi_version().split('.')[0]
    return int(version)


def log_kodi_platform_version():
    """Log our Kodi version and platform for debugging"""
    version = get_kodi_version()
    platform = get_platform()
    log("Kodi %s running on %s" % (version, platform))


def is_valid_addon_version():
    """
    let's filter out the versions of our addons packaged with 'Kodi Boxes'
    that have high version numbers eg. 1001.1.3-2-g661cb6f
    :return:
    """
    version = get_addon_version()
    try:
        major = int(version.split('.')[0])
        if major >= 20:
            return False
        else:
            return True
    except ValueError:
        return False


def is_addon_version_current():
    addon_version = get_addon_version()
    url_params = get_url(sys.argv[2])
    url_version = url_params.get('addon_version')
    if not url_version:
        return False
    return addon_version == url_version


def is_valid_for_report(connection_info, message=None):
    """
    Test if conditions are met to submit a valid error report:
    * IP/host within Australia
    * Not a known VPN provider
    * Add-on version is not from 3rd party
    * Kodi URL is created with current version of add-on (i.e not old favorite)
    :param connection_info: json from ipinfo.io
    :param message: formatted dialog error message
    :return:
    """
    if not message:
        message = format_dialog_message('Issue report denied.')

    from aussieaddonscommon import issue_reporter
    valid_country = issue_reporter.valid_country(connection_info)
    blacklisted_hostname = issue_reporter.blacklisted_hostname(connection_info)

    if not valid_country:
        country_code = connection_info.get('country')
        if country_code:
            from aussieaddonscommon import countries
            country_name = countries.countries.get(country_code, country_code)
            append_message(message,
                           'Your country is reported as {0}, but this '
                           'service is probably geo-blocked to '
                           'Australia.'.format(country_name))
            xbmcgui.Dialog().ok(*message)
            return False

    if blacklisted_hostname:
        append_message(message,
                       'VPN/proxy detected that has been blocked by this '
                       'content provider.')
        xbmcgui.Dialog().ok(*message)
        return False

    if not is_valid_addon_version():
        append_message(message, 'Invalid version number for issue report. ')
        xbmcgui.Dialog().ok(*message)
        return False

    if not is_addon_version_current():
        append_message(message, 'This item appears to be created with a '
                                'different version of this add-on which may '
                                'have caused this error, please '
                                'remove and recreate the link/favorite.')
        return False

    return True


def is_debug():
    try:
        json_query = ('{"jsonrpc":"2.0","id":1,"method":'
                      '"Settings.GetSettingValue","params":'
                      '{"setting":"debug.showloginfo"}}')
        result = json.loads(xbmc.executeJSONRPC(json_query))
        return result['result']['value']
    except RuntimeError:
        return True


def user_report():
    if is_debug():
        from aussieaddonscommon import issue_reporter
        connection_info = issue_reporter.get_connection_info()

        if not is_valid_for_report(connection_info):
            return
        if not xbmcgui.Dialog().yesno('{0} v{1}'.format(
                get_addon_name(), get_addon_version()),
                'Please confirm you would like to submit an issue report '
                'and upload your logfile to Github. '):
            log('Cancelled user report')
            return
        send_report('User initiated report', connection_info=connection_info)
    else:
        dialog_message(['Debug logging not enabled. '
                        'Please enable debug logging, restart Kodi, '
                        'recreate the issue and try again.'])


def send_report(title, trace=None, connection_info=None):
    try:
        dialog_progress = xbmcgui.DialogProgress()
        dialog_created = False
        from aussieaddonscommon import issue_reporter
        log("Reporting issue to GitHub")

        if not connection_info:
            connection_info = issue_reporter.get_connection_info()

        # Show dialog spinner, and close afterwards
        dialog_progress.create('Uploading issue to GitHub...')
        dialog_created = True

        if not issue_reporter.is_supported_addon():
            xbmcgui.Dialog().ok('{0} v{1}'.format(
                get_addon_name(), get_addon_version()),
                'This add-on is no longer supported by Aussie Add-ons.')
            log('Add-on not supported, aborting issue report.')
            return

        report_url = issue_reporter.report_issue(title, trace, connection_info)

        split_url = report_url.replace('/issue-reports', ' /issue-reports')
        dialog_message('Thanks! Your issue has been reported to: {0}\n'
                       'Please visit and describe the issue in order '
                       'for us to assist.'.format(split_url))
        return report_url
    except Exception:
        traceback.print_exc()
        log('Failed to send report')
    finally:
        if dialog_created:
            dialog_progress.close()


def handle_error(message, force=False):
    """Issue reporting handler

    This function should be called in the exception part of a try/catch block
    and provides the user (in some cases) the ability to send an error report.

    Tests are performed to ensure we don't accept some user network type
    errors (like timeouts, etc), any errors from old versions of an add-on or
    any duplicate reports from a user.

    :param force: bypass prevention of reporting when under test
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()

    # Don't show any dialogs when user cancels
    if exc_type.__name__ == 'SystemExit':
        return

    trace = traceback.format_exc()
    log(trace)

    # AttributeError: global name 'foo' is not defined
    error = '{0}: {1}'.format(
        exc_type.__name__, ', '.join(ensure_ascii(e) for e in exc_value.args))

    message = format_dialog_error(message)

    from aussieaddonscommon import issue_reporter

    connection_info = issue_reporter.get_connection_info()

    if not is_valid_for_report(connection_info, message):
        return

    is_reportable = issue_reporter.is_reportable(exc_type,
                                                 exc_value,
                                                 exc_traceback,
                                                 force)

    # If already reported, or a non-reportable error, just show the error
    if not issue_reporter.not_already_reported(error) or not is_reportable:
        xbmcgui.Dialog().ok(*message)
        return

    github_repo = '%s/%s' % (GITHUB_ORG, get_addon_id())
    latest = issue_reporter.get_latest_version(github_repo)
    version = get_addon_version()

    if issue_reporter.is_not_latest_version(version, latest):
        append_message(message,
                       'Your version of this add-on (v{0}) is outdated. '
                       'Please upgrade to the latest version: '
                       'v{1}'.format(version, latest))
        xbmcgui.Dialog().ok(*message)
        return

    if is_reportable:
        append_message(message,
                       'Would you like to automatically '
                       'report this error?')
        if xbmcgui.Dialog().yesno(*message):
            issue_url = send_report(error, trace=trace,
                                    connection_info=connection_info)
            if issue_url:
                report_file = issue_reporter.save_last_error_report(error)
                if report_file:
                    log('Saved error report heading: {0}'.format(report_file))
