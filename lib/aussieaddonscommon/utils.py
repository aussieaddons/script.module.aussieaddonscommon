import htmlentitydefs
import os
import re
import sys
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
    anything other than ascii
    """
    if not isinstance(s, unicode):
        s = str(s)
        s = s.decode("utf-8")
    return unicodedata.normalize('NFC', s).encode('ascii', 'ignore')


def log(s):
    """Logging helper"""
    xbmc.log("[%s v%s] %s" % (get_addon_name(), get_addon_version(),
                              ensure_ascii(s)),
             level=xbmc.LOGNOTICE)


def format_error_summary():
    """Format error summary

    From the traceback, generate a nicely formatted string showing the
    error message.
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()
    return "%s (%d) - %s: %s" % (exc_traceback.tb_frame.f_code.co_name,
                                 exc_traceback.tb_lineno,
                                 exc_type.__name__,
                                 ', '.join(exc_value.args))


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
    content = []
    if title:
        content.append(title)
    else:
        content.append("%s v%s" % (get_addon_name(), get_addon_version()))

    if type(msg) is str:
        msg = msg.split('\n')

    return content + msg


def format_dialog_error(msg=None):
    """Format an error message suitable for a Kodi dialog box"""
    title = "%s v%s ERROR" % (get_addon_name(), get_addon_version())
    return format_dialog_message(format_error_summary(), title=title)


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


def handle_error(message):
    """Issue reporting handler

    This function should be called in the exception part of a try/catch block
    and provides the user (in some cases) the ability to send an error report.

    Tests are performed to ensure we don't accept some user network type
    errors (like timeouts, etc), any errors from old versions of an add-on or
    any duplicate reports from a user.
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()

    # AttributeError: global name 'foo' is not defined
    error_message = '%s: %s' % (exc_type.__name__, ', '.join(exc_value.args))

    traceback_str = traceback.format_exc()
    log(traceback_str)
    report_issue = False

    # Don't show any dialogs when user cancels
    if exc_type.__name__ == 'SystemExit':
        return

    d = xbmcgui.Dialog()
    if d:
        message = format_dialog_error(message)

        # Work out if we should allow an error report
        send_error = can_send_error(error_message)

        # Some transient network errors we don't want any reports about
        ignore_errors = ['The read operation timed out',
                         'IncompleteRead',
                         'getaddrinfo failed',
                         'No address associated with hostname',
                         'Connection reset by peer',
                         'HTTP Error 404: Not Found']

        if any(s in exc_type.__name__ for s in ignore_errors):
            send_error = False

        # Don't allow reporting for these (mostly) user or service errors
        if exc_type.__name__ in ['AussieAddonsNonFatalException']:
            send_error = False

        # Only allow error reporting if the issue_reporting is available
        try:
            import issue_reporter
        except ImportError:
            log('Issue reporter module not available')
            send_error = False

        if send_error:
            try:
                github_repo = 'xbmc-catchuptv-au/%s' % get_addon_id()
                latest_version = issue_reporter.get_latest_version(github_repo)
                version_string = '.'.join([str(i) for i in latest_version])
                if not issue_reporter.is_latest_version(get_addon_version(),
                                                        latest_version):
                    message.append('Your version of this add-on is outdated. '
                                   'Please upgrade to the latest version:'
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
            except Exception as e:
                log('Failed to send error: %s' % str(e))
                message.append('If this error continues to occur, '
                               'please report it to our issue tracker.')
                d.ok(*message)
        else:
            d.ok(*message)

    if report_issue:
        log("Reporting issue to GitHub...")
        issue_url = issue_reporter.report_issue(error_message, traceback_str)

        if issue_url:
            # Split the URL just so it fits better in the dialog window
            split_url = issue_url.replace('/issue-reports', ' /issue-reports')
            d.ok('%s v%s Error' % (get_addon_name(), get_addon_version()),
                 'Thanks! Your issue has been reported to:', split_url)

            # Touch our file to prevent more than one error report
            save_last_error_report(error_message)
