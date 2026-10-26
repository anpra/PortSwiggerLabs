#!/usr/bin/env python3
# Simple content discovery for labs that don't have Burp Pro's "Discover content".
#
# The official solution for some labs assumes Burp Suite Professional, whose
# "Discover content" tool crawls the site and finds hidden paths such as /admin.
# With Burp Community (or no Burp at all) you can get the same result with a
# small wordlist and a script like this one.
#
# Usage:
#   python3 content_discovery.py <host> [wordlist]
#
#   <host>      e.g. 0a03008a042214ef8126b1cb00fb0021.web-security-academy.net
#   [wordlist]  optional file with one path per line (default: a short built-in list)
#
# The script prints every path whose response is NOT 404, so interesting
# endpoints (200, 301, 302, 401, 403) stand out.

import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

# A short list is enough for the Academy labs; most of them hide /admin.
DEFAULT_PATHS = [
    "admin",
    "administrator",
    "admin-panel",
    "admin/login",
    "login",
    "logout",
    "register",
    "my-account",
    "account",
    "dashboard",
    "backup",
    "api",
    "robots.txt",
    "sitemap.xml",
    ".git/config",
]


def fetch(host, path):
    url = "https://%s/%s" % (host, path.lstrip("/"))
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return path, resp.status, resp.headers.get("Location", "")
    except urllib.error.HTTPError as e:
        return path, e.code, e.headers.get("Location", "")
    except Exception as e:  # connection errors, timeouts, etc.
        return path, None, str(e)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 content_discovery.py <host> [wordlist]")
        print("Example: python3 content_discovery.py abc123.web-security-academy.net")
        return 1

    host = sys.argv[1].replace("https://", "").replace("http://", "").strip("/")

    if len(sys.argv) >= 3:
        with open(sys.argv[2]) as f:
            paths = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    else:
        paths = DEFAULT_PATHS

    print("Target: https://%s" % host)
    print("Testing %d paths...\n" % len(paths))

    with ThreadPoolExecutor(max_workers=10) as pool:
        for path, status, extra in pool.map(lambda p: fetch(host, p), paths):
            if status is not None and status != 404:
                location = " -> %s" % extra if extra and extra.startswith("/") else ""
                print("[%s] /%s%s" % (status, path, location))

    print("\nDone. Non-404 paths are the interesting ones.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
