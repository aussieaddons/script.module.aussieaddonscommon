import json
import os
import re
import socket
import sys
import urllib2
import xbmc

from aussieaddonscommon import utils


GITHUB_API_URL = 'https://api.github.com/repos/xbmc-catchuptv-au/issue-reports'
# aussieaddonsbot token
GITHUB_API_TOKEN = '535975f813387efd7df6727a5f8dbbee3718325a'
ISSUE_API_URL = GITHUB_API_URL + '/issues'
GIST_API_URL = 'https://api.github.com/gists'


# Filter out username and passwords from log files
LOG_FILTERS = (
    ('//.+?:.+?@', '//[FILTERED_USER]:[FILTERED_PASSWORD]@'),
    ('<user>.+?</user>', '<user>[FILTERED_USER]</user>'),
    ('<pass>.+?</pass>', '<pass>[FILTERED_PASSWORD]</pass>'),
)


def make_request(url):
    """Make our JSON request to GitHub"""
    return urllib2.Request(url, headers={
        "Authorization": "token %s" % GITHUB_API_TOKEN,
        "Content-Type": "application/json",
    })


def get_public_ip():
    """Get public IP

    Try and fetch the public IP of the reporter for logging
    and reporting purposes
    """
    try:
        result = urllib2.urlopen('http://ipecho.net/plain', timeout=5)
        data = str(result.read())
    except Exception:
        return "Unknown (lookup failure)"

    try:
        ip = re.compile(r'(\d+\.\d+\.\d+\.\d+)').search(data).group(1)
    except Exception:
        return "Unknown (parse failure)"

    try:
        hostname = socket.gethostbyaddr(ip)[0]
        return "%s (%s)" % (ip, hostname)
    except Exception:
        return ip


def get_isp():
    """Get ISP

    Try and fetch the ISP of the reporter for logging
    and reporting purposes
    """
    try:
        result = urllib2.urlopen('http://www.whoismyisp.org', timeout=5)
        data = str(result.read())
    except Exception:
        return "Unknown (lookup failure)"

    try:
        isp = re.compile(r'<h1>(.*)</h1>').search(data).group(1)
    except Exception:
        return "Unknown (parse failure)"

    return isp


def get_xbmc_log():
    """Get XBMC log

    Fetch and read the Kodi log
    """
    log_path = xbmc.translatePath('special://logpath')

    if os.path.isfile(os.path.join(log_path, 'kodi.log')):
        log_file_path = os.path.join(log_path, 'kodi.log')
    elif os.path.isfile(os.path.join(log_path, 'xbmc.log')):
        log_file_path = os.path.join(log_path, 'xbmc.log')
    else:
        # No log file found
        return None

    utils.log("Reading log file from \"%s\"" % log_file_path)
    with open(log_file_path, 'r') as f:
        log_content = f.read()
    for pattern, repl in LOG_FILTERS:
        log_content = re.sub(pattern, repl, log_content)
    return log_content


def get_xbmc_version():
    """Fetch the Kodi build version"""
    try:
        return xbmc.getInfoLabel("System.BuildVersion")
    except Exception:
        return 'Unknown'


def fetch_tags(github_repo):
    """Fetch GitHub tags

    Given a GitHub repo, in the format of username/repository, fetch the list
    of git tags via the API
    """
    api_url = 'https://api.github.com/repos/%s/tags' % github_repo
    return json.load(urllib2.urlopen(api_url))


def get_versions(github_repo):
    """Get versions from tags

    Assemble a list of version from the tags, and split them into lists
    """
    tags = fetch_tags(github_repo)
    tag_names = map(lambda tag: tag['name'], tags)
    versions = filter(lambda tag: re.match(r'v(\d+)\.(\d+)(?:\.(\d+))?', tag),
                      tag_names)
    return map(lambda tag: map(lambda v: int(v), tag[1::].split('.')),
               versions)


def get_latest_version(github_repo):
    """Get latest version tag

    Sort the list, and get the latest version
    """
    versions = get_versions(github_repo)
    return sorted(versions, reverse=True)[0]


def is_latest_version(current_version, latest_version):
    """Is latest version

    Compare current_version (x.x.x string) and latest_version ([x,x,x] list)
    """
    if current_version.startswith('v'):
        current_version = current_version[1::]
    current_version = map(lambda v: int(v), current_version.split('.'))
    return current_version == latest_version


def format_issue(traceback):
    """Build our formatted GitHub issue string"""
    # os.uname() is not available on Windows, so we make this optional.
    try:
        uname = os.uname()
        os_string = ' (%s %s %s)' % (uname[0], uname[2], uname[4])
    except AttributeError:
        os_string = ''

    content = [
        "*Automatic bug report from end-user.*",
        "\n## Environment\n",
        "**Add-on Name:** %s" % utils.get_addon_name(),
        "**Add-on ID:** %s" % utils.get_addon_id(),
        "**Add-on Version:** %s" % utils.get_addon_version(),
        "**Kodi Version:** %s" % get_xbmc_version(),
        "**Python Version:** %s" % sys.version.replace('\n', ''),
        "**Operating System:** %s %s" % (sys.platform, os_string),
        "**IP Address:** %s" % get_public_ip(),
        "**ISP:** %s" % get_isp(),
        "**Kodi URL:** %s" % sys.argv[2],
        "**Python Path:**\n```\n%s\n```" % '\n'.join(sys.path),
        "\n## Traceback\n```\n%s\n```" % traceback,
    ]

    log_url = upload_log()
    if log_url:
        content.append("\n[Full log](%s)" % log_url)

    return "\n".join(content)


def upload_log():
    """Upload our full Kodi log as a GitHub gist"""
    try:
        log_content = get_xbmc_log()
    except Exception as e:
        utils.log("Failed to read log: %s" % e)
        return None

    utils.log("Uploading log file")
    try:
        data = {
            "files": {
                "kodi.log": {
                    "content": log_content
                }
            }
        }
        response = urllib2.urlopen(make_request(GIST_API_URL),
                                   json.dumps(data))
    except urllib2.HTTPError as e:
        utils.log("Failed to save log: HTTPError %s" % e.code)
        return False
    except urllib2.URLError as e:
        utils.log("Failed to save log: URLError %s" % e.reason)
        return False
    try:
        return json.load(response)["html_url"]
    except Exception:
        utils.log("Failed to parse API response: %s" % response.read())


def report_issue(error_message, traceback):
    """Report our issue to GitHub"""

    short_id = utils.get_addon_id().split('.')[-1]

    try:
        data = {
            'title': '[%s] %s' % (short_id, error_message),
            'body': format_issue(traceback),
        }
        response = urllib2.urlopen(make_request(ISSUE_API_URL),
                                   json.dumps(data))
    except urllib2.HTTPError as e:
        utils.log("Failed to report issue: HTTPError %s" % e.code)
        return False
    except urllib2.URLError as e:
        utils.log("Failed to report issue: URLError %s" % e.reason)
        return False
    try:
        return json.load(response)["html_url"]
    except Exception:
        utils.log("Failed to parse API response: %s" % response.read())
