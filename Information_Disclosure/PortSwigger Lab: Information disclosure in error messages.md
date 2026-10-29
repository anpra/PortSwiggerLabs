# PortSwigger Lab: Information disclosure in error messages

# TAGS: Information Disclosure, Error Handling, Stack Trace, Burp Suite

Category: Information Disclosure
Date: October 29, 2026
Day: Thursday
Link: https://portswigger.net/web-security/information-disclosure/exploiting/lab-infoleak-in-error-messages
Published: Ready
Status: Done

---

## Intro

This is the first lab in the **Information Disclosure** series. Information disclosure is when an application leaks details about its internals — framework versions, stack traces, source code, configuration or user data — that the user was never supposed to see. On its own it can look harmless, but it often hands an attacker exactly what they need to exploit something else.

In this lab the flaw is **verbose error handling**: an unhandled exception returns a full stack trace to the client, and that stack trace reveals the exact version of the third-party framework in use — `Apache Struts 2 2.3.31`.

This write-up covers the reconnaissance, the exploitation steps, the root cause, the real-world impact, and how to prevent it.

---

## Reconnaissance:

#### Lab Description Lookup:

The lab description says the application's verbose error messages reveal that it uses a vulnerable version of a third-party framework. The goal is to obtain and submit the version number of that framework.

I opened the store and clicked on a product. The request was:

```http
GET /product?productId=2 HTTP/2
Host: 0aa700c40493eacb80f16c61008e0053.web-security-academy.net
```

The `productId` parameter is clearly typed as an integer on the server side — the first hint that a different data type might break it.

---

## Exploitation:

#### Step 1: Trigger an error with the wrong data type

I sent the product request to **Burp Repeater** and changed `productId` to a non-integer value:

```http
GET /product?productId=example HTTP/2
Host: 0aa700c40493eacb80f16c61008e0053.web-security-academy.net
```

```http
HTTP/2 500 Internal Server Error
Content-Type: text/html; charset=utf-8
```

The application didn't handle the type mismatch, so it threw an exception and returned the full stack trace:

```text
Internal Server Error: java.lang.NumberFormatException: For input string: "example"
    at java.base/java.lang.NumberFormatException.forInputString(NumberFormatException.java:67)
    at java.base/java.lang.Integer.parseInt(Integer.java:661)
    at java.base/java.lang.Integer.parseInt(Integer.java:777)
    at lab.p.l4.x.a.r(Unknown Source)
    at lab.s.j.f.k.t(Unknown Source)
    ...
    at java.base/java.lang.Thread.run(Thread.java:1583)

Apache Struts 2 2.3.31
```

#### Step 2: Extract the framework version

The bottom of the stack trace discloses the framework and its version:

```text
Apache Struts 2 2.3.31
```

#### Step 3: Submit the version

I clicked **Submit solution** on the lab and entered the version number:

```text
2 2.3.31
```

The lab showed **"Congratulations, you solved the lab!"**.

---

## Root Cause

The application runs in a verbose/debug error mode in production. When the `productId` parameter fails to parse as an integer, the exception is not caught, and the default error handler returns the **full Java stack trace** to the client — including internal class names, package structure and the framework banner.

The stack trace also reveals that the app is built on **Apache Struts 2 2.3.31**, a version with publicly known vulnerabilities.

---

## Impact

Knowing the exact framework version lets an attacker look up known CVEs and target them directly. Stack traces also expose internal paths, class names and code structure, which help map the application and craft further attacks. In real incidents, version disclosure of outdated frameworks has been the first step toward remote code execution (for example, Struts 2 exploits).

---

## Remediation

To prevent this issue, applications should:

- Return **generic error pages** to users and never include stack traces, exception messages or framework banners;
- Log the full details **server-side only**, with a correlation ID shown to the user;
- Disable debug/verbose error modes in production;
- Validate input types early and handle parse errors gracefully;
- Keep third-party frameworks patched and remove version banners.

---

## Key Takeaways

1. Type confusion (a string where an integer is expected) is a quick way to trigger unhandled exceptions.
2. Stack traces are a goldmine: framework, version, internal paths and class names.
3. The exact version lets an attacker target known CVEs.
4. Test the error paths, not just the happy path.

---

## References

- [PortSwigger — Information disclosure](https://portswigger.net/web-security/information-disclosure)
- [PortSwigger — Information disclosure in error messages (lab)](https://portswigger.net/web-security/information-disclosure/exploiting/lab-infoleak-in-error-messages)
- [OWASP — Improper Error Handling](https://owasp.org/www-community/Improper_Error_Handling)

---

## Disclaimer

This write-up was created for educational purposes only. All testing was performed in an authorized PortSwigger Web Security Academy laboratory environment. Never test systems without explicit authorization.

This article was written with the assistance of artificial intelligence tools for text review, structure, and grammar correction. However, the entire testing process, technical analysis, vulnerability exploitation, and conclusions presented are the sole responsibility of the author and are based on tests performed in a controlled environment provided by the PortSwigger Web Security Academy.
