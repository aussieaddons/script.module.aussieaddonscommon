import htmlentitydefs
import os
import re
import sys
import textwrap
import traceback
import unicodedata
import urllib
import xbmc
import xbmcaddon
import xbmcgui


ADDON = xbmcaddon.Addon()

# HTML code escape
PATTERN = re.compile("&(\w+?);")


def get_addon_id():
    """Helper function for returning the version of the running add-on"""
    return ADDON.getAddonInfo('id')


def get_addon_name():
    """Helper function for returning the version of the running add-on"""
    return ADDON.getAddonInfo('name')


def get_addon_version():
    """Helper function for returning the version of the running add-on"""
    return ADDON.getAddonInfo('version')


def descape_entity(m, defs=htmlentitydefs.entitydefs):
    """translate one entity to its ISO Latin value"""
    try:
        return defs[m.group(1)]
    except KeyError:
        return m.group(0)  # use as is


def descape(string):
    """translate html chars and ensure ascii"""
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
        v = urllib.unquote_plus(kv[1])
        dict[k] = v
    return dict


def make_url(d):
    """Build a URL suitable for a Kodi add-on from a dict"""
    pairs = []
    for k, v in d.iteritems():
        k = urllib.quote_plus(k)
        v = ensure_ascii(v)
        v = urllib.quote_plus(v)
        pairs.append("%s=%s" % (k, v))
    return "&".join(pairs)


def ensure_ascii(s):
    """Force a string to acsii

    This is especially useful for Kodi menu items which will barf if given
    anything other than ascii"""
    if not isinstance(s, unicode):
        s = str(s)
        s = s.decode("utf-8")
    return unicodedata.normalize('NFC', s).encode('ascii', 'ignore')


def log(s):
    """Logging helper"""
    xbmc.log("[%s v%s] %s" % (get_addon_name(), get_addon_version(),
                              ensure_ascii(s)),
             level=xbmc.LOGNOTICE)


def log_error(message=None):
    """Logging helper for exceptions"""
    exc_type, exc_value, exc_traceback = sys.exc_info()
    if message:
        exc_value = message
    xbmc.log("[%s v%s] ERROR: %s (%d) - %s" %
             (get_addon_name(), get_addon_version(),
              exc_traceback.tb_frame.f_code.co_name, exc_traceback.tb_lineno,
              exc_value), level=xbmc.LOGERROR)
    try:
        xbmc.log(traceback.print_exc(), level=xbmc.LOGERROR)
    except:
        pass


def format_dialog_error(err=None):
    """Format an error message suitable for a Kodi dialog box"""
    # Generate a list of lines for use in XBMC dialog
    msg = ''
    content = []
    exc_type, exc_value, exc_traceback = sys.exc_info()
    content.append("%s v%s Error" % (get_addon_name(), get_addon_version()))
    content.append(str(exc_value))
    if err:
        msg = " - %s" % err
    content.append("%s (%d) %s" % (exc_traceback.tb_frame.f_code.co_name,
                                   exc_traceback.tb_lineno,
                                   msg))
    return content


def format_dialog_message(msg, title=None):
    """Format a message suitable for a Kodi dialog box"""
    if not title:
        title = "%s v%s" % (get_addon_name(), get_addon_version())
    # Add title to the first pos of the textwrap list
    content = textwrap.wrap(msg, 60)
    content.insert(0, title)
    return content


def dialog_message(msg, title=None):
    """Helper function for a simple 'OK' dialog"""
    content = format_dialog_message(msg, title)
    d = xbmcgui.Dialog()
    d.ok(*content)


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
        "XBOX",
        "Windows",
        "ATV2",
        "IOS",
        "OSX",
        "Darwin",
    ]

    for platform in platforms:
        if xbmc.getCondVisibility('System.Platform.'+platform):
            return platform
    return "Unknown"


def get_xbmc_build():
    """Return the Kodi build version"""
    return xbmc.getInfoLabel("System.BuildVersion")


def get_xbmc_version():
    """Return the version number of Kodi"""
    build = get_xbmc_build()
    version = build.split(' ')[0]
    return version


def get_xbmc_major_version():
    """Return the major version number of Kodi"""
    version = get_xbmc_version().split('.')[0]
    return int(version)


def log_xbmc_platform_version():
    """Log our Kodi version and platform for debugging"""
    version = get_xbmc_version()
    platform = get_platform()
    log("Kodi %s running on %s" % (version, platform))


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


def save_last_error_report(trace):
    """Save a copy of our last error report"""
    try:
        rfile = os.path.join(get_file_dir(), 'last_report_error.txt')
        with open(rfile, 'w') as f:
            f.write(trace)
    except Exception:
        log("Error writing error report file")


def can_send_error(trace):
    """Is the user allowed to send this error?

    Check to see if our new error message is different from the last
    successful error report. If it is, or the file doesn't exist, then
    we'll return True
    """
    try:
        rfile = os.path.join(get_file_dir(), 'last_report_error.txt')

        if not os.path.isfile(rfile):
            return True
        else:
            f = open(rfile, 'r')
            report = f.read()
            if report != trace:
                return True
    except Exception:
        log("Error checking error report file")

    log("Not allowing error report. Last report matches this one")
    return False


def handle_error(msg, exc=None):
    """Issue reporting handler

    This function should be called in the exception part of a try/catch block
    and provides the user (in some cases) the ability to send an error report.

    Tests are performed to ensure we don't accept some user network type
    errors (like timeouts, etc), any errors from old versions of an add-on or
    any duplicate reports from a user.
    """
    traceback_str = traceback.format_exc()
    log(traceback_str)
    report_issue = False

    # Don't show any dialogs when user cancels
    if 'SystemExit' in traceback_str:
        return

    d = xbmcgui.Dialog()
    if d:
        message = format_dialog_error(msg)

        # Work out if we should allow an error report
        send_error = can_send_error(traceback_str)

        # Some transient network errors we don't want any reports about
        ignore_errors = ['The read operation timed out',
                         'IncompleteRead',
                         'getaddrinfo failed',
                         'No address associated with hostname',
                         'Connection reset by peer',
                         'HTTP Error 404: Not Found']

        if any(s in traceback_str for s in ignore_errors):
            send_error = False

        # Don't allow reporting for these (mostly) user or service errors
        if type(exc).__name__ in ['AussieAddonsNonFatalException']:
            send_error = False

        # Only allow error reporting if the issue_reporting is available
        try:
            import issue_reporter
        except ImportError:
            log('Issue reporter module not available')
            send_error = False

        if send_error:
            latest_version = issue_reporter.get_latest_version()
            version_string = '.'.join([str(i) for i in latest_version])
            if not issue_reporter.is_latest_version(get_addon_version(),
                                                    latest_version):
                message.append('Your version of this add-on is outdated. '
                               'Please try upgrading to the latest version: '
                               'v%s' % version_string)
                d.ok(*message)
                return

            # Only report if we haven't done one already
            try:
                message.append('Would you like to automatically '
                               'report this error?')
                report_issue = d.yesno(*message)
            except Exception:
                message.append('If this error continues to occur, '
                               'please report it to our issue tracker.')
                d.ok(*message)
        else:
            # Just show the message
            d.ok(*message)

    if report_issue:
        log("Reporting issue to GitHub...")
        issue_url = issue_reporter.report_issue(traceback_str)
        if issue_url:
            # Split the url here to make sure it fits in our dialog
            split_url = issue_url.replace('/xbmc', ' /xbmc')
            d.ok('%s v%s Error' % (get_addon_name(), get_addon_version()),
                 'Thanks! Your issue has been reported to: %s' % split_url)

            # Touch our file to prevent more than one error report
            save_last_error_report(traceback_str)
